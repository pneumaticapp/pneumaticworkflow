from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import ObjectDoesNotExist
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action
from rest_framework.exceptions import (
    AuthenticationFailed,
    ValidationError,
)
from rest_framework.viewsets import GenericViewSet

from src.accounts.enums import SourceType
from src.analysis.mixins import BaseIdentifyMixin
from src.authentication.messages import MSG_AU_0003
from src.authentication.permissions import MSAuthPermission
from src.authentication.serializers import (
    MSTokenSerializer,
)
from src.authentication.services.exceptions import (
    AuthException,
)
from src.authentication.services.microsoft import (
    MicrosoftAuthService,
)
from src.authentication.services.user_auth import (
    AuthService,
)
from src.authentication.tasks import update_microsoft_contacts
from src.authentication.throttling import (
    AuthMSAuthUriThrottle,
    AuthMSTokenThrottle,
)
from src.authentication.views.mixins import (
    SignUpMixin,
    SSORestrictionMixin,
)
from src.generics.mixins.views import CustomViewSetMixin
from src.logs.events import AuditEventService
from src.logs.events.enums import LoginFailedReason
from src.openapi.serializers import AuthTokenResponseSerializer
from src.openapi.responses import (
    EMPTY,
    FORBIDDEN,
    TOO_MANY_REQUESTS,
    UNAUTHORIZED,
    VALIDATION_ERROR,
)
from src.openapi.internal_serializers import AuthUriResponseSerializer
from src.utils.logging import (
    SentryLogLevel,
    capture_sentry_message,
)
from src.utils.validation import raise_validation_error

UserModel = get_user_model()


class MSAuthViewSet(
    SSORestrictionMixin,
    SignUpMixin,
    CustomViewSetMixin,
    BaseIdentifyMixin,
    GenericViewSet,
):
    permission_classes = (MSAuthPermission,)
    audit_source = SourceType.MICROSOFT
    serializer_class = MSTokenSerializer

    @property
    def throttle_classes(self):
        if self.action == 'token':
            return (AuthMSTokenThrottle,)
        if self.action == 'auth_uri':
            return (AuthMSAuthUriThrottle,)
        return ()

    @extend_schema(
        tags=['Auth'],
        summary='Exchange a Microsoft authorization code',
        description=(
            'No existing session is required; Microsoft authentication must '
            'be enabled. Forward code, state, client_info and session_state '
            'from the provider callback. Signs in an existing user or '
            'creates an account when signup is enabled. Returns a '
            'Pneumatic Bearer session token.'
        ),
        auth=[],
        parameters=[MSTokenSerializer],
        responses={
            200: AuthTokenResponseSerializer,
            400: VALIDATION_ERROR,
            401: UNAUTHORIZED,
            403: FORBIDDEN,
            429: TOO_MANY_REQUESTS,
        },
    )
    @action(methods=('GET',), detail=False)
    def token(self, request, *args, **kwargs):
        slz = self.get_serializer(data=request.GET)
        slz.is_valid(raise_exception=True)
        try:
            service = MicrosoftAuthService()
            user_data = service.get_user_data(
                auth_response={
                    'code': slz.validated_data['code'],
                    'client_info': slz.validated_data['client_info'],
                    'state': slz.validated_data['state'],
                    'session_state': slz.validated_data['session_state'],
                },
            )
        except AuthException as ex:
            raise_validation_error(message=ex.message)
        else:
            is_signup = False
            try:
                user = UserModel.objects.active().get(email=user_data['email'])
                self.check_sso_restrictions(user)
                token = AuthService.get_auth_token(
                    user=user,
                    user_agent=request.headers.get(
                        'User-Agent',
                        request.META.get('HTTP_USER_AGENT'),
                    ),
                    user_ip=request.META.get('HTTP_X_REAL_IP'),
                )
            except ObjectDoesNotExist as ex:
                if settings.PROJECT_CONF['SIGNUP']:
                    user, token = self.signup(
                        **user_data,
                        utm_source=slz.validated_data.get('utm_source'),
                        utm_medium=slz.validated_data.get('utm_medium'),
                        utm_campaign=slz.validated_data.get('utm_campaign'),
                        utm_term=slz.validated_data.get('utm_term'),
                        utm_content=slz.validated_data.get('utm_content'),
                        gclid=slz.validated_data.get('gclid'),
                    )
                    is_signup = True
                else:
                    AuditEventService.login_failed(
                        reason=LoginFailedReason.SIGNUP_DISABLED,
                        email=user_data['email'],
                    )
                    raise AuthenticationFailed(MSG_AU_0003) from ex
            except ValidationError:
                AuditEventService.login_failed(
                    reason=LoginFailedReason.SSO_REQUIRED,
                    email=user.email,
                )
                raise
            service.apply_photo_to_user(user, user_data)
            service.save_tokens_for_user(user)
            update_microsoft_contacts.delay(user.id)
            if not is_signup:
                AuditEventService.user_logged_in(
                    user=user,
                    source=self.audit_source,
                )
            return self.response_ok({'token': token})

    @extend_schema(
        tags=['Auth'],
        summary='Get the Microsoft authorization URL',
        description=(
            'No existing session is required. Microsoft authentication must '
            'be enabled. Redirect the browser to auth_uri, then forward '
            'the provider callback parameters to the token endpoint.'
        ),
        auth=[],
        responses={
            200: AuthUriResponseSerializer,
            400: VALIDATION_ERROR,
            401: UNAUTHORIZED,
            403: FORBIDDEN,
            429: TOO_MANY_REQUESTS,
        },
    )
    @action(methods=('GET',), detail=False, url_path='auth-uri')
    def auth_uri(self, request, *args, **kwargs):
        try:
            service = MicrosoftAuthService()
            auth_uri = service.get_auth_uri()
        except AuthException as ex:
            raise_validation_error(message=ex.message)
        else:
            return self.response_ok({
                'auth_uri': auth_uri,
            })

    @extend_schema(
        tags=['Auth'],
        summary='Acknowledge the Microsoft logout callback',
        description=(
            'Logs the callback without expiring a Pneumatic token. Requires '
            'the Microsoft authentication feature; no existing user '
            'session is required.'
        ),
        auth=[],
        responses={204: EMPTY, 401: UNAUTHORIZED, 403: FORBIDDEN},
    )
    @action(methods=('GET',), detail=False)
    def logout(self, *args, **kwargs):
        capture_sentry_message(
            message='Microsoft logout request',
            data=self.request.GET,
            level=SentryLogLevel.INFO,
        )
        return self.response_ok()
