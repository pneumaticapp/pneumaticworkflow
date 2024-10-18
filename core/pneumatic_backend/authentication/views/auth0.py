from django.contrib.auth import get_user_model
from django.db.models import ObjectDoesNotExist
from django.conf import settings
from rest_framework.viewsets import GenericViewSet
from rest_framework.decorators import action
from rest_framework.exceptions import AuthenticationFailed
from pneumatic_backend.generics.mixins.views import CustomViewSetMixin
from pneumatic_backend.authentication.permissions import Auth0Permission
from pneumatic_backend.analytics.mixins import BaseIdentifyMixin
from pneumatic_backend.authentication.services.user_auth import (
    AuthService
)
from pneumatic_backend.authentication.services.exceptions import (
    AuthException
)
from pneumatic_backend.authentication.services.auth0 import (
    Auth0Service
)
from pneumatic_backend.authentication.serializers import (
    Auth0TokenSerializer,
)
from pneumatic_backend.authentication.views.mixins import SignUpMixin
from pneumatic_backend.utils.validation import raise_validation_error
from pneumatic_backend.authentication.throttling import (
    Auth0AuthUriThrottle,
    Auth0TokenThrottle,
)
from pneumatic_backend.utils.logging import (
    capture_sentry_message,
    SentryLogLevel,
)
from pneumatic_backend.authentication.messages import MSG_AU_0003


UserModel = get_user_model()


class Auth0ViewSet(
    SignUpMixin,
    CustomViewSetMixin,
    BaseIdentifyMixin,
    GenericViewSet
):
    permission_classes = (Auth0Permission,)
    serializer_class = Auth0TokenSerializer

    @property
    def throttle_classes(self):
        if self.action == 'token':
            return (Auth0TokenThrottle,)
        elif self.action == 'auth_uri':
            return (Auth0AuthUriThrottle,)
        return ()

    @action(methods=('GET',), detail=False)
    def token(self, request, *args, **kwargs):
        slz = self.get_serializer(data=request.GET)
        slz.is_valid(raise_exception=True)
        try:
            service = Auth0Service()
            user_data = service.get_user_data(
                auth_response={
                    'code': slz.validated_data['code'],
                    'state': slz.validated_data['state'],
                }
            )
        except AuthException as ex:
            raise_validation_error(message=ex.message)
        else:
            try:
                user = UserModel.objects.active().get(email=user_data['email'])
                token = AuthService.get_auth_token(
                    user=user,
                    user_agent=request.headers.get(
                        'User-Agent',
                        request.META.get('HTTP_USER_AGENT')
                    ),
                    user_ip=request.META.get('HTTP_X_REAL_IP'),
                )
            except ObjectDoesNotExist:
                if settings.PROJECT_CONF['SIGNUP']:
                    user, token = self.signup(
                        **user_data,
                        utm_source=slz.validated_data.get('utm_source'),
                        utm_medium=slz.validated_data.get('utm_medium'),
                        utm_campaign=slz.validated_data.get('utm_campaign'),
                        utm_term=slz.validated_data.get('utm_term'),
                        utm_content=slz.validated_data.get('utm_content'),
                        gclid=slz.validated_data.get('gclid'),
                    )
                else:
                    raise AuthenticationFailed(MSG_AU_0003)
            service.save_tokens_for_user(user)
            return self.response_ok({'token': token})

    @action(methods=('GET',), detail=False, url_path='auth-uri')
    def auth_uri(self, request, *args, **kwargs):
        try:
            service = Auth0Service()
            auth_uri = service.get_auth_uri()
        except AuthException as ex:
            raise_validation_error(message=ex.message)
        else:
            return self.response_ok({
                'auth_uri': auth_uri
            })

    @action(methods=('GET',), detail=False)
    def logout(self, *args, **kwargs):
        capture_sentry_message(
            message='Auth0 logout request',
            data=self.request.GET,
            level=SentryLogLevel.INFO
        )
        return self.response_ok()
