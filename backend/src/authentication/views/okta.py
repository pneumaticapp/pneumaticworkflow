from django.contrib.auth import get_user_model
from rest_framework.decorators import action
from rest_framework.viewsets import GenericViewSet

from src.analysis.mixins import BaseIdentifyMixin
from src.authentication.permissions import OktaPermission
from src.authentication.serializers import (
    OktaTokenSerializer,
)
from src.authentication.services.exceptions import (
    AuthException,
)
from src.authentication.services.okta import (
    OktaService,
)
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


class OktaViewSet(
    CustomViewSetMixin,
    BaseIdentifyMixin,
    GenericViewSet,
):
    permission_classes = (OktaPermission,)
    serializer_class = OktaTokenSerializer

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
            service = OktaService(request=request)
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
            self.identify(user)
            return self.response_ok({'token': token})

    @action(methods=('GET',), detail=False, url_path='auth-uri')
    def auth_uri(self, request, *args, **kwargs):
        try:
            service = OktaService()
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
            message='Okta logout request',
            data=self.request.GET,
            level=SentryLogLevel.INFO,
        )
        return self.response_ok()
