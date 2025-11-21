from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import ObjectDoesNotExist
from rest_framework.decorators import action
from rest_framework.exceptions import (
    AuthenticationFailed,
)
from rest_framework.generics import (
    CreateAPIView,
    get_object_or_404,
)
from rest_framework.viewsets import GenericViewSet
from rest_framework_simplejwt.tokens import TokenError

from src.accounts.enums import (
    SourceType,
    UserInviteStatus,
    UserStatus,
)
from src.accounts.tokens import (
    AuthToken,
    VerificationToken,
)
from src.analysis.mixins import BaseIdentifyMixin
from src.analysis.services import AnalyticService
from src.authentication.enums import AuthTokenType
from src.authentication.messages import (
    MSG_AU_0001,
    MSG_AU_0002,
    MSG_AU_0003,
)
from src.authentication.permissions import (
    GoogleAuthPermission,
)
from src.authentication.serializers import (
    GoogleTokenSerializer,
    SignInWithGoogleSerializer,
)
from src.authentication.services.exceptions import AuthException
from src.authentication.services.google import GoogleAuthService
from src.authentication.services.user_auth import AuthService
from src.authentication.tasks import update_google_contacts
from src.authentication.throttling import (
    AuthGoogleAuthUriThrottle,
    AuthGoogleTokenThrottle,
)
from src.authentication.views.mixins import (
    SignUpMixin,
    SSORestrictionMixin,
)
from src.generics.mixins.views import (
    BaseResponseMixin,
    CustomViewSetMixin,
)
from src.services.email import EmailService
from src.utils.logging import (
    SentryLogLevel,
    capture_sentry_message,
)
from src.utils.validation import raise_validation_error

UserModel = get_user_model()


class GoogleAuthViewSet(
    SSORestrictionMixin,
    SignUpMixin,
    CustomViewSetMixin,
    BaseIdentifyMixin,
    GenericViewSet,
):
    permission_classes = (
        GoogleAuthPermission,
    )
    serializer_class = GoogleTokenSerializer

    @property
    def throttle_classes(self):
        if self.action == 'token':
            return (AuthGoogleTokenThrottle,)
        if self.action == 'auth_uri':
            return (AuthGoogleAuthUriThrottle,)
        return ()

    # TODO: Remove in https://my.pneumatic.app/workflows/28206/
    def create(self, request, *args, **kwargs):
        token = str(AuthToken.for_auth_data(**request.data))
        return self.response_ok({'token': token})

    # TODO: Remove in https://my.pneumatic.app/workflows/28206/
    def list(self, request, *args, **kwargs):
        try:
            token_decoded = AuthToken(token=request.GET.get('token'))
        except TokenError:
            raise_validation_error(message=MSG_AU_0001)
        try:
            instance = UserModel.objects.get(
                status=UserStatus.ACTIVE,
                email=token_decoded.get('email'),
            )
            self.identify(instance)
            self.group(instance)
            token = AuthService.get_auth_token(
                user=instance,
                user_agent=request.headers.get(
                    'User-Agent',
                    request.META.get('HTTP_USER_AGENT'),
                ),
                user_ip=request.META.get('HTTP_X_REAL_IP'),
            )
            return self.response_ok({'token': token})
        except UserModel.DoesNotExist:
            pass
        response = token_decoded.payload
        response.pop('jti')
        response.pop('exp')
        return self.response_ok(response)

    @action(methods=('GET',), detail=False)
    def token(self, request, *args, **kwargs):
        slz = self.get_serializer(data=request.GET)
        slz.is_valid(raise_exception=True)

        try:
            service = GoogleAuthService()
            user_data = service.get_user_data(
                auth_response={
                    'code': slz.validated_data['code'],
                    'state': slz.validated_data['state'],
                },
            )
        except AuthException as ex:
            raise_validation_error(message=ex.message)
        else:
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
            except ObjectDoesNotExist as err:
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
                else:
                    raise AuthenticationFailed(MSG_AU_0003) from err

            service.save_tokens_for_user(user)
            update_google_contacts.delay(user.id)
            return self.response_ok({'token': token})

    @action(methods=('GET',), detail=False, url_path='auth-uri')
    def auth_uri(self, request, *args, **kwargs):
        try:
            service = GoogleAuthService()
            auth_uri = service.get_auth_uri()
        except AuthException as ex:
            raise_validation_error(message=ex.message)
        else:
            return self.response_ok({
                'auth_uri': auth_uri,
            })

    @action(methods=('GET',), detail=False)
    def logout(self, *args, **kwargs):
        capture_sentry_message(
            message='Google logout request',
            data=self.request.GET,
            level=SentryLogLevel.INFO,
        )
        return self.response_ok({})


class SignInWithGoogleView(
    CreateAPIView,
    BaseIdentifyMixin,
    BaseResponseMixin,
):
    permission_classes = (GoogleAuthPermission,)
    serializer_class = SignInWithGoogleSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = get_object_or_404(
            UserModel.objects.active(),
            email=serializer.validated_data['email'],
        )
        if user.account.is_verification_timed_out():
            owner = user.account.get_owner()
            EmailService.send_verification_email(
                user=owner,
                token=str(VerificationToken.for_user(owner)),
                logo_lg=user.account.logo_lg,
            )
            raise AuthenticationFailed(MSG_AU_0002(owner.email))
        invite = user.invite
        if invite:
            invite.status = UserInviteStatus.ACCEPTED
            invite.save(update_fields=['status'])

        self.identify(user)
        AnalyticService.users_logged_in(
            user=user,
            is_superuser=request.is_superuser,
            auth_type=AuthTokenType.USER,
            source=SourceType.GOOGLE,
        )

        token = AuthService.get_auth_token(
            user=user,
            user_agent=request.headers.get(
                'User-Agent',
                request.META.get('HTTP_USER_AGENT'),
            ),
            user_ip=request.META.get('HTTP_X_REAL_IP'),
        )
        return self.response_ok({'token': token})
