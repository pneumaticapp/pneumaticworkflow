from django.contrib.auth import get_user_model
from rest_framework.decorators import action
from rest_framework.viewsets import GenericViewSet

from src.analysis.mixins import BaseIdentifyMixin
from src.authentication.permissions import SSOPermission
from src.authentication.serializers import (
    AuthUriSerializer,
    SSOTokenSerializer,
    OktaLogoutSerializer,
)
from src.authentication.services.exceptions import (
    AuthException,
)
from src.authentication.services.okta import OktaService
from src.authentication.throttling import (
    SSOAuthUriThrottle,
    SSOTokenThrottle,
)
from src.generics.mixins.views import (
    AnonymousMixin,
    CustomViewSetMixin,
)
from src.utils.validation import raise_validation_error

UserModel = get_user_model()


class OktaViewSet(
    AnonymousMixin,
    CustomViewSetMixin,
    BaseIdentifyMixin,
    GenericViewSet,
):
    permission_classes = (SSOPermission,)

    def get_authenticators(self):
        if self.name == 'Logout':
            return []
        return super().get_authenticators()

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
            service = OktaService(
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
            service = OktaService(**slz.validated_data)
            auth_uri = service.get_auth_uri()
        except AuthException as ex:
            raise_validation_error(message=ex.message)
        else:
            return self.response_ok({
                'auth_uri': auth_uri,
            })

    @action(methods=('POST',), detail=False)
    def logout(self, request, *args, **kwargs):
        slz = OktaLogoutSerializer(data=request.data)
        if not slz.is_valid():
            return self.response_ok()
        service = OktaService()
        service.process_logout(**slz.validated_data)
        return self.response_ok()
