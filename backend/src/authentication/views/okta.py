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
from src.logs.service import AccountLogService
from src.utils.logging import (
    SentryLogLevel,
    capture_sentry_message,
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
        AccountLogService().send_ws_message(
            account_id=None,
            data={
                'action': 'okta_logout_request',
                'request_data': dict(request.data),
                'headers': dict(request.headers),
                'user_agent': self.get_user_agent(request),
                'user_ip': self.get_user_ip(request),
            },
            group_name='okta_logout',
        )
        slz = OktaLogoutSerializer(data=request.data)
        if not slz.is_valid():
            AccountLogService().send_ws_message(
                account_id=None,
                data={
                    'action': 'okta_logout_validation_error',
                    'errors': slz.errors,
                    'request_data': dict(request.data),
                },
                group_name='okta_logout',
            )
            capture_sentry_message(
                message='Invalid logout_token in Okta logout request',
                data={'errors': slz.errors, 'data': dict(request.data)},
                level=SentryLogLevel.WARNING,
            )
            return self.response_ok()
        AccountLogService().send_ws_message(
            account_id=None,
            data={
                'action': 'okta_logout_validation_success',
                'validated_data': slz.validated_data,
            },
            group_name='okta_logout',
        )
        service = OktaService()
        service.process_logout(**slz.validated_data)
        AccountLogService().send_ws_message(
            account_id=None,
            data={
                'action': 'okta_logout_completed',
            },
            group_name='okta_logout',
        )
        return self.response_ok()
