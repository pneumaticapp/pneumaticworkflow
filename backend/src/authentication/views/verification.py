from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework.generics import (
    CreateAPIView,
    ListAPIView,
    get_object_or_404,
)
from rest_framework_simplejwt.exceptions import TokenError

from src.accounts.permissions import UserIsAdminOrAccountOwner
from src.accounts.tokens import (
    VerificationToken,
)
from src.analysis.services import AnalyticService
from src.authentication.enums import AuthTokenType
from src.authentication.messages import MSG_AU_0008
from src.authentication.permissions import (
    PrivateApiPermission,
)
from src.authentication.serializers import TokenSerializer
from src.generics.mixins.views import (
    BaseResponseMixin,
)
from src.generics.permissions import (
    UserIsAuthenticated,
)
from src.services.email import EmailService
from src.utils.validation import raise_validation_error

UserModel = get_user_model()


class VerificationTokenView(
    ListAPIView,
    BaseResponseMixin,
):
    permission_classes = (PrivateApiPermission,)
    serializer_class = TokenSerializer

    def list(self, request, *args, **kwargs):
        slz = self.get_serializer(data=request.GET)
        slz.is_valid(raise_exception=True)
        try:
            token_data = VerificationToken(token=slz.validated_data['token'])
        except TokenError:
            raise_validation_error(message=MSG_AU_0008)
        user = get_object_or_404(
            UserModel.objects.active(),
            id=token_data['user_id'],
        )
        account = user.account
        if not account.is_verified:
            account.is_verified = True
            account.save(update_fields=['is_verified'])
            AnalyticService.account_verified(
                user=user,
                is_superuser=request.is_superuser,
                auth_type=AuthTokenType.USER,
            )
        return self.response_ok()


class VerificationTokenResendView(
    CreateAPIView,
    BaseResponseMixin,
):
    permission_classes = (
        UserIsAuthenticated,
        UserIsAdminOrAccountOwner,
        PrivateApiPermission,
    )

    def create(self, request, *args, **kwargs):
        user = request.user.account.users.get(is_account_owner=True)

        if settings.VERIFICATION_CHECK and not user.account.is_verified:
            EmailService.send_verification_email(
                user=user,
                token=str(VerificationToken.for_user(user)),
                logo_lg=user.account.logo_lg,
            )

        return self.response_ok({'email': user.email})
