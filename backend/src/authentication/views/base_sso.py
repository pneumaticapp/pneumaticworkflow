from rest_framework.decorators import action
from rest_framework.viewsets import GenericViewSet

from src.analysis.mixins import BaseIdentifyMixin
from src.authentication.serializers import (
    AuthUriSerializer,
    SSOTokenSerializer,
)
from src.authentication.services.exceptions import AuthException
from src.authentication.throttling import (
    SSOAuthUriThrottle,
    SSOTokenThrottle,
)
from src.generics.mixins.views import (
    AnonymousMixin,
    CustomViewSetMixin,
)
from src.utils.validation import raise_validation_error


class BaseSSOViewSet(
    AnonymousMixin,
    CustomViewSetMixin,
    BaseIdentifyMixin,
    GenericViewSet,
):

    """ The two endpoints every SSO provider has: where to send the
        browser, and the token of the callback.

        A provider view names its service_class and its
        permission_classes; the rest is the same for all of them. The
        sign in event is published by the service
        (BaseSSOService._complete_authentication), where the new and
        the returning person are told apart. """

    service_class = None

    @property
    def throttle_classes(self):
        if self.action == 'token':
            return (SSOTokenThrottle,)
        if self.action == 'auth_uri':
            return (SSOAuthUriThrottle,)
        return ()

    @action(methods=('GET',), detail=False)
    def token(self, request, *args, **kwargs):
        slz = SSOTokenSerializer(data=request.GET)
        slz.is_valid(raise_exception=True)
        try:
            service = self.service_class(
                domain=slz.validated_data.get('domain'),
            )
            user, token = service.authenticate_user(
                **slz.validated_data,
                user_agent=self.get_user_agent(request),
                user_ip=self.get_user_ip(request),
            )
        except AuthException as ex:
            raise_validation_error(message=ex.message)
        else:
            self.identify(user)
            return self.response_ok({'token': token})

    @action(methods=('GET',), detail=False, url_path='auth-uri')
    def auth_uri(self, request, *args, **kwargs):
        slz = AuthUriSerializer(data=request.GET)
        slz.is_valid(raise_exception=True)
        try:
            service = self.service_class(**slz.validated_data)
            auth_uri = service.get_auth_uri()
        except AuthException as ex:
            raise_validation_error(message=ex.message)
        else:
            return self.response_ok({
                'auth_uri': auth_uri,
            })
