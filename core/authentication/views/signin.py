from django.contrib.auth import get_user_model, authenticate
from rest_framework.exceptions import (
    AuthenticationFailed,
)
from rest_framework.generics import (
    get_object_or_404,
    CreateAPIView,
)
from rest_framework.permissions import AllowAny
from pneumatic_backend.accounts.tokens import (
    VerificationToken,
)
from pneumatic_backend.authentication.enums import AuthTokenType
from pneumatic_backend.accounts.enums import SourceType
from pneumatic_backend.services.email import EmailService
from pneumatic_backend.authentication.permissions import (
    PrivateApiPermission,
    IsSuperuserPermission
)
from pneumatic_backend.authentication.services import AuthService
from pneumatic_backend.authentication.messages import (
    MSG_AU_0002,
    MSG_AU_0003,
)
from pneumatic_backend.generics.mixins.views import (
    BaseResponseMixin
)
from pneumatic_backend.analytics.mixins import BaseIdentifyMixin
from pneumatic_backend.analytics.services import AnalyticService


UserModel = get_user_model()


class TokenObtainPairCustomView(
    CreateAPIView,
    BaseIdentifyMixin,
    BaseResponseMixin,
):
    permission_classes = (AllowAny,)
    authentication_classes = []

    def post(self, request, *args, **kwargs):
        user = authenticate(**request.data)

        if not user:
            raise AuthenticationFailed(MSG_AU_0003)

        if user.account.is_verification_timed_out():
            owner = user.account.users.get(is_account_owner=True)
            EmailService.send_verification_email(
                user=owner,
                token=str(VerificationToken.for_user(owner)),
                logo_lg=user.account.logo_lg
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
                request.META.get('HTTP_USER_AGENT')
            ),
            user_ip=request.META.get('HTTP_X_REAL_IP'),
        )
        return self.response_ok({'token': token})


class SuperuserEmailTokenView(
    CreateAPIView,
    BaseResponseMixin,
):
    permission_classes = (PrivateApiPermission, IsSuperuserPermission)

    def create(self, request, *args, **kwargs):
        email = request.data.get('email')
        user = get_object_or_404(UserModel.objects.active(), email=email)
        token = AuthService.get_superuser_auth_token(user)
        return self.response_ok({'token': token})
