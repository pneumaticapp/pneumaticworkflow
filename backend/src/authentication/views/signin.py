from django.contrib.auth import authenticate, get_user_model
from drf_spectacular.utils import (
    OpenApiExample,
    extend_schema,
    extend_schema_view,
)
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework.exceptions import (
    AuthenticationFailed,
    ValidationError,
)
from rest_framework.generics import (
    CreateAPIView,
    get_object_or_404,
)
from rest_framework.permissions import AllowAny

from src.accounts.enums import SourceType
from src.accounts.tokens import (
    VerificationToken,
)
from src.analysis.mixins import BaseIdentifyMixin
from src.analysis.services import AnalyticService
from src.authentication.enums import AuthTokenType
from src.authentication.messages import (
    MSG_AU_0002,
    MSG_AU_0003,
)
from src.authentication.permissions import (
    IsSuperuserPermission,
    PrivateApiPermission,
)
from src.authentication.services.user_auth import AuthService
from src.authentication.views.mixins import SSORestrictionMixin
from src.generics.mixins.views import (
    BaseResponseMixin,
)
from src.logs.events import AuditEventService
from src.logs.events.enums import LoginFailedReason
from src.notifications.tasks import send_verification_notification
from src.openapi.responses import SSO_VALIDATION_ERROR
from src.openapi.serializers import AuthTokenResponseSerializer
from src.openapi.responses import (
    FIELD_VALIDATION_ERROR,
    FORBIDDEN,
    NOT_FOUND,
    UNAUTHORIZED,
)
from src.openapi.internal_serializers import (
    CredentialsRequestSerializer,
    EmailAddressSerializer,
)

UserModel = get_user_model()


class TokenObtainPairCustomView(
    SSORestrictionMixin,
    CreateAPIView,
    BaseIdentifyMixin,
    BaseResponseMixin,
):
    permission_classes = (AllowAny,)
    authentication_classes = []

    @extend_schema(
        tags=['Auth'],
        summary='Sign in with email and password',
        description=(
            'No user token is required. Send the account email in username '
            'and its password. Returns a Pneumatic session token for '
            'Authorization: Bearer. Invalid credentials or expired account '
            'verification are rejected; SSO-only accounts cannot use '
            'password sign-in. User-Agent identifies the created session.'
        ),
        auth=[],
        request=CredentialsRequestSerializer,
        responses={
            200: AuthTokenResponseSerializer,
            400: SSO_VALIDATION_ERROR,
            403: FORBIDDEN,
        },
        examples=[OpenApiExample(
            'Password sign-in',
            value={
                'username': 'person@example.com',
                'password': 'account-password',
            },
            request_only=True,
        )],
    )
    def post(self, request, *args, **kwargs):
        user = authenticate(**request.data)

        if not user:
            AuditEventService.login_failed(
                reason=LoginFailedReason.BAD_CREDENTIALS,
                email=request.data.get('username'),
            )
            raise AuthenticationFailed(MSG_AU_0003)

        try:
            self.check_sso_restrictions(user)
        except ValidationError:
            AuditEventService.login_failed(
                reason=LoginFailedReason.SSO_REQUIRED,
                email=user.email,
            )
            raise

        if user.account.is_verification_timed_out():
            owner = user.account.users.get(is_account_owner=True)
            send_verification_notification.delay(
                user_id=owner.id,
                user_email=owner.email,
                account_id=owner.account_id,
                user_first_name=owner.first_name,
                token=str(VerificationToken.for_user(owner)),
                logo_lg=user.account.logo_lg,
            )
            AuditEventService.login_failed(
                reason=LoginFailedReason.VERIFICATION_EXPIRED,
                email=user.email,
            )
            raise AuthenticationFailed(MSG_AU_0002(owner.email))

        self.identify(user)
        AnalyticService.users_logged_in(
            user=user,
            is_superuser=False,
            auth_type=AuthTokenType.USER,
            source=SourceType.EMAIL,
        )
        token = AuthService.get_auth_token(
            user=user,
            user_agent=request.headers.get(
                'User-Agent',
                request.META.get('HTTP_USER_AGENT'),
            ),
            user_ip=request.META.get('HTTP_X_REAL_IP'),
        )
        AuditEventService.user_logged_in(
            user=user,
            source=SourceType.EMAIL,
        )
        return self.response_ok({'token': token})


@extend_schema_view(
    post=extend_schema(
        tags=['Auth'],
        summary='Refresh JWT token',
        description='Exchange a valid refresh token for a new access token.',
        responses={
            200: TokenRefreshSerializer,
            400: FIELD_VALIDATION_ERROR,
            401: UNAUTHORIZED,
        },
    ),
)
class AuthTokenRefreshView(TokenRefreshView):
    pass


@extend_schema_view(
    post=extend_schema(
        tags=['Auth'],
        summary='Create an impersonation token',
        description=(
            'Internal operation. Requires an authenticated superuser and '
            'PrivateApiPermission (the configured source-IP restrictions). '
            'With PRIVATE_API_CHECK_IP enabled, API keys are rejected '
            'even from allowlisted IPs. '
            'Looks up an active user by email and returns an impersonation '
            'token; the action is audited.'
        ),
        request=EmailAddressSerializer,
        responses={
            200: AuthTokenResponseSerializer,
            401: UNAUTHORIZED,
            403: FORBIDDEN,
            404: NOT_FOUND,
        },
    ),
)
class SuperuserEmailTokenView(
    CreateAPIView,
    BaseResponseMixin,
):
    permission_classes = (PrivateApiPermission, IsSuperuserPermission)

    def create(self, request, *args, **kwargs):
        email = request.data.get('email')
        user = get_object_or_404(UserModel.objects.active(), email=email)
        token = AuthService.get_superuser_auth_token(user)
        AuditEventService.superuser_logged_in_as(
            user=request.user,
            auth_type=request.token_type,
            target=user,
        )
        return self.response_ok({'token': token})
