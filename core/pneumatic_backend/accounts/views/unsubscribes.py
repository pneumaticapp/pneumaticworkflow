from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.exceptions import TokenError
from pneumatic_backend.generics.mixins.views import (
    BaseResponseMixin
)
from pneumatic_backend.accounts.tokens import (
    DigestUnsubscribeToken,
    UnsubscribeEmailToken,
)
from pneumatic_backend.analytics.services import AnalyticService
from pneumatic_backend.authentication.enums import AuthTokenType
from pneumatic_backend.accounts.messages import (
    MSG_A_0008,
    MSG_A_0014,
)

UserModel = get_user_model()


class UnsubscribeDigestView(
    ListAPIView,
    BaseResponseMixin
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


class UnsubscribeEmailView(
    ListAPIView,
    BaseResponseMixin
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
