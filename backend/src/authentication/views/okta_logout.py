from drf_spectacular.utils import OpenApiExample, extend_schema
from rest_framework.serializers import ValidationError
from rest_framework.views import APIView

from src.authentication.permissions import SSOPermission
from src.authentication.serializers import OktaLogoutSerializer
from src.authentication.tasks import process_okta_logout
from src.generics.mixins.views import (
    AnonymousMixin,
    BaseResponseMixin,
)
from src.openapi.responses import EMPTY, FORBIDDEN
from src.utils.logging import (
    SentryLogLevel,
    capture_sentry_message,
)


class OktaLogoutView(
    AnonymousMixin,
    BaseResponseMixin,
    APIView,
):
    """
    View for handling Okta Back-Channel Logout requests.

    Okta sends its logout JWT as a Bearer token in Authorization.
    This token must be validated to ensure the request is authentic.
    """

    permission_classes = (SSOPermission,)

    def get_authenticators(self):
        """
        No authentication required for logout endpoint.

        Bearer token validation is performed inside the Celery task
        by verifying the logout_token with Okta API.
        This approach allows us to:
        1. Respond quickly to Okta (204 No Content)
        2. Process validation and logout asynchronously
        3. Handle errors without blocking Okta's request

        The bearer token from Authorization header contains JWT that must
        be validated against Okta's public keys to ensure request authenticity.
        """
        return []

    @extend_schema(
        tags=['Auth'],
        summary='Receive an Okta back-channel logout notification',
        description=(
            'Requires SSO to be enabled. Authorization: Bearer must contain '
            'the provider logout JWT, not a Pneumatic session token. JSON '
            'sub_id includes format plus the provider identity (iss/sub '
            'for iss_sub, or email for email). Valid structures are queued '
            'for asynchronous JWT verification and logout. A 204 only '
            'acknowledges receipt: malformed structures or missing/invalid '
            'Bearer headers are logged and also acknowledged with 204.'
        ),
        auth=[{'oktaLogoutAuth': []}],
        request=OktaLogoutSerializer,
        responses={204: EMPTY, 403: FORBIDDEN},
        examples=[OpenApiExample(
            'Email identity',
            value={'sub_id': {
                'format': 'email',
                'email': 'person@example.com',
            }},
            request_only=True,
        )],
    )
    def post(self, request, *args, **kwargs):
        """
        Process Okta Back-Channel Logout request.

        Returns 204 No Content to acknowledge receipt.
        Actual processing happens asynchronously in Celery task.

        Serializer does basic structure validation only.
        After logout_token verification, we trust Okta's data.
        """
        slz = OktaLogoutSerializer(data=request.data)
        try:
            slz.is_valid(raise_exception=True)
        except ValidationError as ex:
            # Log invalid requests but still return 204 OK
            # We process only valid JSON structure requests to avoid
            # processing malformed or malicious data
            capture_sentry_message(
                message='Invalid Okta logout request structure',
                level=SentryLogLevel.WARNING,
                data={
                    'request_data': request.data,
                    'error': str(ex),
                },
            )
            return self.response_ok()

        auth_header = request.headers.get('Authorization', '').split()
        if len(auth_header) != 2 or auth_header[0].lower() != 'bearer':
            capture_sentry_message(
                message='Missing or invalid Authorization header',
                level=SentryLogLevel.WARNING,
                data={'auth_header': auth_header},
            )
            return self.response_ok()
        process_okta_logout.delay(
            logout_token=auth_header[1],
            logout_format=slz.validated_data['format'],
            data=slz.validated_data['data'],
        )
        return self.response_ok()
