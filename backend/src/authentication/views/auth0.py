from django.contrib.auth import get_user_model
from rest_framework.decorators import action
from rest_framework.viewsets import GenericViewSet

from src.analysis.mixins import BaseIdentifyMixin
from src.authentication.permissions import SSOPermission
from src.authentication.serializers import (
    Auth0TokenSerializer,
    AuthUriSerializer,
)
from src.authentication.services.auth0 import Auth0Service
from src.authentication.services.exceptions import (
    AuthException,
)
from src.authentication.tasks import update_auth0_contacts
from src.authentication.throttling import (
    Auth0AuthUriThrottle,
    Auth0TokenThrottle,
)
from src.generics.mixins.views import CustomViewSetMixin
from src.utils.logging import (
    SentryLogLevel,
    capture_sentry_message,
)
from src.utils.validation import raise_validation_error

UserModel = get_user_model()


class Auth0ViewSet(
    CustomViewSetMixin,
    BaseIdentifyMixin,
    GenericViewSet,
):
    permission_classes = (SSOPermission,)
    serializer_class = Auth0TokenSerializer

    @property
    def throttle_classes(self):
        if self.action == 'token':
            return (Auth0TokenThrottle,)
        if self.action == 'auth_uri':
            return (Auth0AuthUriThrottle,)
        return ()

    @action(methods=('GET',), detail=False)
    def token(self, request, *args, **kwargs):
        slz = self.get_serializer(data=request.GET)
        slz.is_valid(raise_exception=True)
        try:
            service = Auth0Service(request=request)
            user, token = service.authenticate_user(
                auth_response={
                    'code': slz.validated_data['code'],
                    'state': slz.validated_data['state'],
                },
                utm_source=slz.validated_data.get('utm_source'),
                utm_medium=slz.validated_data.get('utm_medium'),
                utm_term=slz.validated_data.get('utm_term'),
                utm_content=slz.validated_data.get('utm_content'),
                gclid=slz.validated_data.get('gclid'),
                utm_campaign=slz.validated_data.get('utm_campaign'),
            )
        except AuthException as ex:
            raise_validation_error(message=ex.message)
        else:
            update_auth0_contacts.delay(user.id)
            return self.response_ok({'token': token})

    @action(methods=('GET',), detail=False, url_path='auth-uri')
    def auth_uri(self, request, *args, **kwargs):
        slz = AuthUriSerializer(data=request.GET)
        slz.is_valid(raise_exception=True)
        try:
            service = Auth0Service(**slz.validated_data)
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
            message='Auth0 logout request',
            data=self.request.GET,
            level=SentryLogLevel.INFO,
        )
        return self.response_ok()
