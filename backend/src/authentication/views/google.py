from django.conf import settings
from rest_framework.decorators import action
from rest_framework.viewsets import GenericViewSet

from src.accounts.enums import SourceType
from src.analysis.mixins import BaseIdentifyMixin
from src.authentication.permissions import (
    GoogleAuthPermission,
)
from src.authentication.serializers import (
    GoogleTokenSerializer,
)
from src.authentication.services.exceptions import AuthException
from src.authentication.services.google import GoogleAuthService
from src.authentication.tasks import update_google_contacts
from src.authentication.throttling import (
    AuthGoogleAuthUriThrottle,
    AuthGoogleTokenThrottle,
)
from src.authentication.views.mixins import (
    LoginEventMixin,
    SignUpMixin,
    SSORestrictionMixin,
)
from src.generics.mixins.views import (
    CustomViewSetMixin,
)
from src.utils.logging import (
    SentryLogLevel,
    capture_sentry_message,
)
from src.utils.validation import raise_validation_error


class GoogleAuthViewSet(
    SSORestrictionMixin,
    SignUpMixin,
    LoginEventMixin,
    CustomViewSetMixin,
    BaseIdentifyMixin,
    GenericViewSet,
):
    permission_classes = (
        GoogleAuthPermission,
    )
    serializer_class = GoogleTokenSerializer
    source = SourceType.GOOGLE

    @property
    def throttle_classes(self):
        if self.action == 'token':
            return (AuthGoogleTokenThrottle,)
        if self.action == 'auth_uri':
            return (AuthGoogleAuthUriThrottle,)
        return ()

    @action(methods=('GET',), detail=False)
    def token(self, request, *args, **kwargs):
        slz = self.get_serializer(data=request.GET)
        slz.is_valid(raise_exception=True)

        try:
            service = GoogleAuthService()
            user_data = service.get_user_data(
                auth_response={
                    'code': slz.validated_data['code'],
                    'state': slz.validated_data['state'],
                },
            )
        except AuthException as ex:
            raise_validation_error(message=ex.message)
        else:
            user, token = self._login_or_signup(
                request=request,
                user_data=user_data,
                validated_data=slz.validated_data,
                signup_enabled=settings.PROJECT_CONF['SIGNUP'],
            )
            service.save_tokens_for_user(user)
            update_google_contacts.delay(user.id)
            return self.response_ok({'token': token})

    @action(methods=('GET',), detail=False, url_path='auth-uri')
    def auth_uri(self, request, *args, **kwargs):
        try:
            service = GoogleAuthService()
            auth_uri = service.get_auth_uri()
        except AuthException as ex:
            raise_validation_error(message=ex.message)
        else:
            return self.response_ok({
                'auth_uri': auth_uri,
            })

    @action(methods=('GET',), detail=False)
    def logout(self, *args, **kwargs):
        capture_sentry_message(
            message='Google logout request',
            data=self.request.GET,
            level=SentryLogLevel.INFO,
        )
        return self.response_ok({})
