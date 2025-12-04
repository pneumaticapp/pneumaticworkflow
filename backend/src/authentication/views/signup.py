from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework.generics import (
    CreateAPIView,
    RetrieveAPIView,
)

from src.accounts.tokens import (
    VerificationToken,
)
from src.analysis.mixins import BaseIdentifyMixin
from src.authentication.permissions import (
    PrivateApiPermission,
    SignupPermission,
)
from src.authentication.serializers import (
    SecuredSignUpSerializer,
    SignUpSerializer,
)
from src.authentication.views.mixins import SignUpMixin
from src.generics.mixins.views import (
    AnonymousAccountMixin,
    BaseResponseMixin,
)
from src.notifications.tasks import send_verification_notification

UserModel = get_user_model()


class SignUpView(
    SignUpMixin,
    CreateAPIView,
    RetrieveAPIView,
    AnonymousAccountMixin,
    BaseResponseMixin,
    BaseIdentifyMixin,
):
    model = UserModel
    serializer_class = SignUpSerializer
    permission_classes = (
        PrivateApiPermission,
        SignupPermission,
    )

    def retrieve(self, request, *args, **kwargs):
        if not settings.PROJECT_CONF['CAPTCHA']:
            show_captcha = False
        else:
            account_exists = self.anonymous_user_account_exists(request)
            show_captcha = account_exists in {True, None}
        return self.response_ok({'show_captcha': show_captcha})

    def after_signup(self, user: UserModel):
        account = user.account
        if settings.VERIFICATION_CHECK and not account.is_verified:
            send_verification_notification.delay(
                user_id=user.id,
                user_email=user.email,
                account_id=account.id,
                user_first_name=user.first_name,
                token=str(VerificationToken.for_user(user)),
                logo_lg=account.logo_lg,
            )
        self.inc_anonymous_user_account_counter(self.request)

    def create(self, request, *args, **kwargs):
        account_exists = self.anonymous_user_account_exists(request)
        captcha_required = account_exists in {True, None}
        if settings.PROJECT_CONF['CAPTCHA'] and captcha_required:
            serializer_cls = SecuredSignUpSerializer
        else:
            serializer_cls = SignUpSerializer
        slz = serializer_cls(
            data=request.data,
            context={"request": request},  # for ReCaptchaV2Field
        )
        slz.is_valid(raise_exception=True)
        _, token = self.signup(**slz.validated_data)
        return self.response_ok({'token': token})
