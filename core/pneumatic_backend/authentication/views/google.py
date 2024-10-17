from django.contrib.auth import get_user_model
from rest_framework.exceptions import (
    AuthenticationFailed,
)
from rest_framework.viewsets import GenericViewSet
from rest_framework.generics import (
    get_object_or_404,
    CreateAPIView,
)
from pneumatic_backend.authentication.permissions import GoogleAuthPermission
from rest_framework_simplejwt.tokens import TokenError
from pneumatic_backend.authentication.enums import AuthTokenType
from pneumatic_backend.accounts.enums import (
    UserInviteStatus,
    UserStatus,
    SourceType,
)
from pneumatic_backend.accounts.tokens import (
    AuthToken,
    VerificationToken,
)
from pneumatic_backend.services.email import EmailService
from pneumatic_backend.analytics.services import AnalyticService
from pneumatic_backend.authentication.permissions import (
    PrivateApiPermission,
)
from pneumatic_backend.authentication.services import AuthService
from pneumatic_backend.authentication.messages import (
    MSG_AU_0001,
    MSG_AU_0002,
)
from pneumatic_backend.generics.mixins.views import (
    CustomViewSetMixin,
    BaseResponseMixin
)
from pneumatic_backend.authentication.serializers import (
    SignInWithGoogleSerializer,
)
from pneumatic_backend.analytics.mixins import BaseIdentifyMixin
from pneumatic_backend.utils.validation import raise_validation_error


UserModel = get_user_model()


class GoogleAuthViewSet(
    CustomViewSetMixin,
    BaseIdentifyMixin,
    GenericViewSet
):
    permission_classes = (
        GoogleAuthPermission,
        PrivateApiPermission,
    )

    def create(self, request, *args, **kwargs):
        token = str(AuthToken.for_auth_data(**request.data))
        return self.response_ok({'token': token})

    def list(self, request, *args, **kwargs):
        try:
            token_decoded = AuthToken(token=request.GET.get('token'))
        except TokenError:
            raise_validation_error(message=MSG_AU_0001)
        try:
            instance = UserModel.objects.get(
                status=UserStatus.ACTIVE,
                email=token_decoded.get('email')
            )
            self.identify(instance)
            self.group(instance)
            token = AuthService.get_auth_token(
                user=instance,
                user_agent=request.headers.get(
                    'User-Agent',
                    request.META.get('HTTP_USER_AGENT')
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
            email=serializer.validated_data['email']
        )
        if user.account.is_verification_timed_out():
            owner = user.account.get_owner()
            EmailService.send_verification_email(
                user=owner,
                token=str(VerificationToken.for_user(owner)),
                logo_lg=user.account.logo_lg
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
                request.META.get('HTTP_USER_AGENT')
            ),
            user_ip=request.META.get('HTTP_X_REAL_IP'),
        )
        return self.response_ok({'token': token})
