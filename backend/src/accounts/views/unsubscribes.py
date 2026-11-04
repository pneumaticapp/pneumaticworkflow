from django.conf import settings
from django.contrib.auth import get_user_model
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiParameter,
    extend_schema,
    extend_schema_view,
)
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.exceptions import TokenError

from src.accounts.messages import (
    MSG_A_0008,
    MSG_A_0014,
)
from src.accounts.tokens import (
    DigestUnsubscribeToken,
    UnsubscribeEmailToken,
)
from src.analysis.enums import MailoutType
from src.analysis.services import AnalyticService
from src.authentication.enums import AuthTokenType
from src.generics.mixins.views import (
    BaseResponseMixin,
)
from src.logs.events import AuditEventService

UserModel = get_user_model()


@extend_schema_view(
    get=extend_schema(
        tags=['Accounts'],
        summary='Unsubscribe from workflow digest emails',
        description=(
            'Email-link operation requiring no session. A valid token '
            'turns off workflow digests for its user. Returns an HTML '
            'status message and a script redirecting to the frontend after '
            'three seconds. Missing/invalid tokens also return HTML 200 '
            'with an error message; this is not an HTTP 302 redirect.'
        ),
        auth=[],
        parameters=[OpenApiParameter(
            name='token',
            location=OpenApiParameter.QUERY,
            type=OpenApiTypes.STR,
            description='Signed unsubscribe token from the email link.',
        )],
        responses={(200, 'text/html'): OpenApiTypes.STR},
    ),
)
class UnsubscribeDigestView(
    ListAPIView,
    BaseResponseMixin,
):
    permission_classes = (AllowAny,)

    def list(self, request, *args, **kwargs):
        token = request.GET.get('token')
        message = MSG_A_0014
        if token:
            try:
                token_data = DigestUnsubscribeToken(token=token)
                user = UserModel.objects.get(id=token_data['user_id'])
                user.is_digest_subscriber = False
                user.save(update_fields=['is_digest_subscriber'])
                AnalyticService.users_digest(
                    user=user,
                    is_superuser=False,
                    auth_type=AuthTokenType.USER,
                )
                AuditEventService.user_unsubscribed(
                    user=user,
                    email_type=MailoutType.MAP[MailoutType.WF_DIGEST],
                )
            except TokenError:
                message = MSG_A_0008
        else:
            message = MSG_A_0008
        redirect_script = f"""
        <script>
            setTimeout("location.href = '{settings.FRONTEND_URL}';",3000);
        </script>
        {message}
        """
        return self.response_raw(redirect_script)


@extend_schema_view(
    get=extend_schema(
        tags=['Accounts'],
        summary='Unsubscribe from the email category in an email link',
        description=(
            'Email-link operation requiring no session. The signed token '
            'selects the user and email preference to disable. Returns an '
            'HTML status message with a scripted frontend redirect after '
            'three seconds. Missing/invalid tokens also return HTML 200 '
            'with an error message.'
        ),
        auth=[],
        parameters=[OpenApiParameter(
            name='token',
            location=OpenApiParameter.QUERY,
            type=OpenApiTypes.STR,
            description='Signed unsubscribe token from the email link.',
        )],
        responses={(200, 'text/html'): OpenApiTypes.STR},
    ),
)
class UnsubscribeEmailView(
    ListAPIView,
    BaseResponseMixin,
):
    permission_classes = (AllowAny,)

    def list(self, request, *args, **kwargs):
        token = request.GET.get('token')
        message = MSG_A_0014
        if token:
            try:
                token_data = UnsubscribeEmailToken(token=token)
                user = UserModel.objects.get(id=token_data['user_id'])
                email_type = token_data['email_type']
                setattr(user, email_type, False)
                user.save(update_fields=[email_type])
                AuditEventService.user_unsubscribed(
                    user=user,
                    email_type=email_type,
                )
            except TokenError:
                message = MSG_A_0008
        else:
            message = MSG_A_0008
        redirect_script = f"""
        <script>
            setTimeout("location.href = '{settings.FRONTEND_URL}';",3000);
        </script>
        {message}
        """
        return self.response_raw(redirect_script)
