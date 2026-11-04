from django.conf import settings
from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema, extend_schema_view
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
from src.logs.events import AuditEventService
from src.notifications.tasks import send_verification_notification
from src.openapi.responses import (
    EMPTY,
    FORBIDDEN,
    NOT_FOUND,
    UNAUTHORIZED,
    VALIDATION_ERROR,
)
from src.openapi.internal_serializers import EmailAddressSerializer
from src.utils.validation import raise_validation_error

UserModel = get_user_model()


@extend_schema_view(
    get=extend_schema(
        tags=['Auth'],
        summary='Verify the account email address',
        description=(
            'Consumes the verification token from the email and marks the '
            'account verified. No user session is required; private API '
            'source-IP restrictions apply. Reusing a valid token for an '
            'already verified account succeeds without further changes.'
        ),
        auth=[],
        parameters=[TokenSerializer],
        responses={
            204: EMPTY,
            400: VALIDATION_ERROR,
            401: UNAUTHORIZED,
            403: FORBIDDEN,
            404: NOT_FOUND,
        },
    ),
)
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
            AuditEventService.account_verified(user=user)
        return self.response_ok()


@extend_schema_view(
    post=extend_schema(
        tags=['Auth'],
        summary='Resend the account verification email',
        description=(
            'Requires a non-guest account admin/owner and private API '
            'source-IP restrictions. Returns the account owner email; '
            'sends a new message only while verification is enabled and '
            'the account remains unverified.'
        ),
        request=None,
        responses={
            200: EmailAddressSerializer,
            401: UNAUTHORIZED,
            403: FORBIDDEN,
        },
    ),
)
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
            send_verification_notification.delay(
                user_id=user.id,
                user_email=user.email,
                account_id=user.account_id,
                user_first_name=user.first_name,
                token=str(VerificationToken.for_user(user)),
                logo_lg=user.account.logo_lg,
            )
            AuditEventService.verification_resent(
                user=request.user,
                auth_type=request.token_type,
                account_owner=user,
            )

        return self.response_ok({'email': user.email})
