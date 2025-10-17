from django.contrib.auth import authenticate, get_user_model
from rest_framework.exceptions import (
    AuthenticationFailed,
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
from src.analytics.mixins import BaseIdentifyMixin
from src.analytics.services import AnalyticService
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
from src.generics.mixins.views import (
    BaseResponseMixin,
)
from src.services.email import EmailService

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
                logo_lg=user.account.logo_lg,
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
