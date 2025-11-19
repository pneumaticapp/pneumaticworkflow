from django.contrib.auth import get_user_model
from rest_framework.decorators import action
from rest_framework.generics import (
    CreateAPIView,
    get_object_or_404,
)
from rest_framework.permissions import AllowAny
from rest_framework.viewsets import GenericViewSet
from rest_framework_simplejwt.exceptions import TokenError

from src.accounts.services.user import UserService
from src.accounts.tokens import (
    ResetPasswordToken,
)
from src.authentication.enums import (
    ResetPasswordStatus,
)
from src.authentication.permissions import (
    PrivateApiPermission,
)
from src.authentication.serializers import (
    ChangePasswordSerializer,
    ConfirmPasswordSerializer,
    ResetPasswordSerializer,
    TokenSerializer,
)
from src.authentication.mixins import SSORestrictionMixin
from src.authentication.services.user_auth import AuthService
from src.authentication.throttling import (
    AuthResetPasswordThrottle,
)
from src.authentication.tokens import PneumaticToken
from src.generics.mixins.views import (
    BaseResponseMixin,
    CustomViewSetMixin,
)
from src.generics.permissions import (
    UserIsAuthenticated,
)
from src.notifications.tasks import (
    send_reset_password_notification,
)

UserModel = get_user_model()


class ResetPasswordViewSet(
    SSORestrictionMixin,
    CustomViewSetMixin,
    GenericViewSet,
):
    permission_classes = (AllowAny,)
    action_serializer_classes = {
        'create': ResetPasswordSerializer,
        'list': TokenSerializer,
        'confirm': ConfirmPasswordSerializer,
    }

    @property
    def throttle_classes(self):
        return (AuthResetPasswordThrottle, )

    def create(self, request):
        slz = self.get_serializer(data=request.data)
        slz.is_valid(raise_exception=True)
        self.check_sso_restrictions(slz.validated_data['email'])
        user = UserModel.objects.select_related('account').filter(
            email=slz.validated_data['email'],
        ).active().only('id', 'email', 'account__logo_lg').first()
        if user:
            send_reset_password_notification.delay(
                user_id=user.id,
                user_email=user.email,
                logo_lg=user.account.logo_lg,
                logging=user.account.log_api_requests,
                account_id=user.account_id,
            )
        return self.response_ok()

    def list(self, request, *args, **kwargs):
        slz = self.get_serializer(data=request.GET)
        slz.is_valid(raise_exception=True)
        try:
            ResetPasswordToken(slz.validated_data['token'])
        except TokenError:
            return self.response_ok({'status': ResetPasswordStatus.INVALID})

        return self.response_ok({'status': ResetPasswordStatus.VALID})

    @action(methods=['post'], detail=False)
    def confirm(self, request):
        slz = self.get_serializer(data=request.data)
        slz.is_valid(raise_exception=True)
        token_data = ResetPasswordToken(token=slz.validated_data['token'])

        user = get_object_or_404(
            UserModel.objects.active(),
            id=token_data['user_id'],
        )
        self.check_sso_restrictions(user.email)
        service = UserService(user=user)
        service.change_password(password=slz.validated_data['new_password'])
        PneumaticToken.expire_all_tokens(user)
        token = AuthService.get_auth_token(
            user=user,
            user_agent=request.headers.get(
                'User-Agent',
                request.META.get('HTTP_USER_AGENT'),
            ),
            user_ip=request.META.get('HTTP_X_REAL_IP'),
        )
        return self.response_ok({'token': token})


class ChangePasswordView(
    SSORestrictionMixin,
    CreateAPIView,
    BaseResponseMixin,
):
    serializer_class = ChangePasswordSerializer
    permission_classes = (
        UserIsAuthenticated,
        PrivateApiPermission,
    )

    def get_serializer_context(self, **kwargs):
        context = super().get_serializer_context()
        context['user'] = self.request.user
        return context

    def create(self, request, *args, **kwargs):
        self.check_sso_restrictions(request.user.email)
        slz = self.get_serializer(data=request.data)
        slz.is_valid(raise_exception=True)
        service = UserService(user=request.user)
        service.change_password(password=slz.validated_data['new_password'])
        PneumaticToken.expire_all_tokens(request.user)
        token = PneumaticToken.create(
            request.user,
            user_agent=request.user_agent,
            user_ip=request.META.get('HTTP_X_REAL_IP'),
        )
        return self.response_ok({'token': token})
