from django.contrib.auth import authenticate, get_user_model
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework_simplejwt.views import TokenRefreshView
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
from src.authentication.enums import (
    AuthTokenType,
    LoginFailedReason,
)
from src.authentication.messages import (
    MSG_AU_0002,
    MSG_AU_0003,
)
from src.authentication.permissions import (
    IsSuperuserPermission,
    PrivateApiPermission,
)
from src.authentication.serializers import (
    SuperuserEmailTokenSerializer,
)
from src.authentication.services.user_auth import AuthService
from src.authentication.views.mixins import (
    LoginEventMixin,
    SSORestrictionMixin,
)
from src.generics.mixins.views import (
    BaseResponseMixin,
)
from src.logs.events import AuditEventService
from src.notifications.tasks import send_verification_notification
from src.utils.http import (
    get_client_ip,
    get_user_agent_header,
)

UserModel = get_user_model()


class TokenObtainPairCustomView(
    SSORestrictionMixin,
    LoginEventMixin,
    CreateAPIView,
    BaseIdentifyMixin,
    BaseResponseMixin,
):
    permission_classes = (AllowAny,)
    authentication_classes = []
    source = SourceType.EMAIL

    def post(self, request, *args, **kwargs):
        user = authenticate(**request.data)

        if not user:
            self.emit_login_failed(
                request=request,
                reason=LoginFailedReason.BAD_CREDENTIALS,
            )
            raise AuthenticationFailed(MSG_AU_0003)

        try:
            self.check_sso_restrictions(user)
        except ValidationError:
            self.emit_login_failed(
                request=request,
                reason=LoginFailedReason.SSO_REQUIRED,
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
            self.emit_login_failed(
                request=request,
                reason=LoginFailedReason.VERIFICATION_EXPIRED,
            )
            raise AuthenticationFailed(MSG_AU_0002(owner.email))

        self.identify(user)
        AnalyticService.users_logged_in(
            user=user,
            is_superuser=False,
            auth_type=AuthTokenType.USER,
            source=self.source,
        )
        token = AuthService.get_auth_token(
            user=user,
            user_agent=get_user_agent_header(request),
            user_ip=get_client_ip(request),
        )
        self.emit_login(user=user, request=request)
        return self.response_ok({'token': token})


@extend_schema_view(
    post=extend_schema(
        tags=['Auth'],
        summary='Refresh JWT token',
        description='Exchange a valid refresh token for a new access token.',
    ),
)
class AuthTokenRefreshView(TokenRefreshView):
    pass


@extend_schema(exclude=True)
class SuperuserEmailTokenView(
    CreateAPIView,
    BaseResponseMixin,
):
    permission_classes = (PrivateApiPermission, IsSuperuserPermission)
    serializer_class = SuperuserEmailTokenSerializer

    def create(self, request, *args, **kwargs):
        slz = self.get_serializer(data=request.data)
        slz.is_valid(raise_exception=True)
        user = get_object_or_404(
            UserModel.objects.active(),
            email=slz.validated_data['email'],
        )
        token = AuthService.get_superuser_auth_token(user)
        AuditEventService.superuser_logged_in_as(
            request=request,
            user=user,
            reason=slz.validated_data.get('reason'),
        )
        return self.response_ok({'token': token})
