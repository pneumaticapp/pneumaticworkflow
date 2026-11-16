from django.conf import settings
from django.contrib.auth import get_user_model
from drf_spectacular.utils import (
    OpenApiExample,
    extend_schema,
    extend_schema_view,
)
from rest_framework.generics import (
    CreateAPIView,
    RetrieveAPIView,
)

from src.accounts.enums import SourceType
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
from src.logs.events import AuditEventService
from src.notifications.tasks import send_verification_notification
from src.openapi.serializers import AuthTokenResponseSerializer
from src.openapi.responses import FORBIDDEN, UNAUTHORIZED, VALIDATION_ERROR
from src.openapi.internal_serializers import (
    SignUpRequestSerializer,
    SignupCaptchaResponseSerializer,
)

UserModel = get_user_model()


@extend_schema_view(
    get=extend_schema(
        tags=['Auth'],
        summary='Check signup captcha requirement',
        description=(
            'Returns whether the next signup from this visitor requires '
            'captcha. Signup must be enabled. Private API source-IP '
            'restrictions apply when configured; no user session is needed.'
        ),
        auth=[],
        responses={
            200: SignupCaptchaResponseSerializer,
            401: UNAUTHORIZED,
            403: FORBIDDEN,
        },
    ),
    post=extend_schema(
        tags=['Auth'],
        summary='Register an account and its owner',
        description=(
            'Creates an account and owner, then returns a Pneumatic session '
            'token. Requires signup to be enabled and PrivateApiPermission '
            'source-IP rules to pass. Check GET /auth/signup first; include '
            'captcha when show_captcha=true. A verification email is sent '
            'when account verification is enabled.'
        ),
        auth=[],
        request=SignUpRequestSerializer,
        responses={
            200: AuthTokenResponseSerializer,
            400: VALIDATION_ERROR,
            401: UNAUTHORIZED,
            403: FORBIDDEN,
        },
        examples=[OpenApiExample(
            'Signup without captcha',
            value={
                'email': 'person@example.com',
                'first_name': 'Jane',
                'last_name': 'Doe',
                'password': 'account-password',
                'company_name': 'Example company',
            },
            request_only=True,
        )],
    ),
)
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
    audit_source = SourceType.EMAIL

    def retrieve(self, request, *args, **kwargs):
        if not settings.PROJECT_CONF['CAPTCHA']:
            show_captcha = False
        else:
            account_exists = self.anonymous_user_account_exists(request)
            show_captcha = account_exists in {True, None}
        return self.response_ok({'show_captcha': show_captcha})

    def after_signup(self, user: UserModel):

        """ No super(): the account log row and the Slack ping of
            the mixin belong to the SSO sign ups, an e-mail sign up
            leaves the journal entry only. """

        AuditEventService.user_signed_up(
            user=user,
            source=self.audit_source,
        )
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
