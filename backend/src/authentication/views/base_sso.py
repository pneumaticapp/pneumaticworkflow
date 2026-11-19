from drf_spectacular.utils import extend_schema
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
from src.openapi.serializers import AuthTokenResponseSerializer
from src.openapi.responses import (
    FORBIDDEN,
    TOO_MANY_REQUESTS,
    UNAUTHORIZED,
    VALIDATION_ERROR,
)
from src.openapi.internal_serializers import AuthUriResponseSerializer
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

    @extend_schema(
        tags=['Auth'],
        summary='Exchange an SSO authorization code',
        description=(
            'No existing session is required. SSO must be enabled for this '
            'deployment. After redirecting to auth_uri, forward the callback '
            'code and unchanged state to this endpoint. State identifies '
            'the SSO domain. Returns a Pneumatic Bearer session token.'
        ),
        auth=[],
        parameters=[SSOTokenSerializer],
        responses={
            200: AuthTokenResponseSerializer,
            400: VALIDATION_ERROR,
            401: UNAUTHORIZED,
            403: FORBIDDEN,
            429: TOO_MANY_REQUESTS,
        },
    )
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

    @extend_schema(
        tags=['Auth'],
        summary='Get the SSO authorization URL',
        description=(
            'No existing session is required. SSO must be enabled. Supply '
            'domain for the account SSO configuration when needed, then '
            'redirect the browser to the returned auth_uri. Preserve the '
            'provider state for the code exchange.'
        ),
        auth=[],
        parameters=[AuthUriSerializer],
        responses={
            200: AuthUriResponseSerializer,
            400: VALIDATION_ERROR,
            401: UNAUTHORIZED,
            403: FORBIDDEN,
            429: TOO_MANY_REQUESTS,
        },
    )
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
