from rest_framework.serializers import ValidationError
from rest_framework.views import APIView

from src.authentication.permissions import SSOPermission
from src.authentication.serializers import OktaLogoutSerializer
from src.authentication.tasks import process_okta_logout
from src.generics.mixins.views import (
    AnonymousMixin,
    BaseResponseMixin,
)
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

    Okta sends logout_token as a bearer token in the request body.
    This token must be validated to ensure the request is authentic.
    """

    permission_classes = (SSOPermission,)

    def get_authenticators(self):
        """
        No authentication required for logout endpoint.

        Bearer token validation is performed inside the Celery task
        by verifying the logout_token with Okta API.
        This approach allows us to:
        1. Respond quickly to Okta (200 OK)
        2. Process validation and logout asynchronously
        3. Handle errors without blocking Okta's request
        """
        return []

    def post(self, request, *args, **kwargs):
        """
        Process Okta Back-Channel Logout request.

        Always returns 200 OK to acknowledge receipt.
        Actual processing happens asynchronously in Celery task.

        Serializer does basic structure validation only.
        After logout_token verification, we trust Okta's data.
        """
        slz = OktaLogoutSerializer(data=request.data)
        try:
            slz.is_valid(raise_exception=True)
        except ValidationError as ex:
            # Log invalid requests but still return 200 OK
            # Okta doesn't retry on errors, so we always acknowledge
            capture_sentry_message(
                message='Invalid Okta logout request structure',
                level=SentryLogLevel.WARNING,
                data={
                    'request_data': request.data,
                    'error': str(ex),
                },
            )
            return self.response_ok()

        # Extract logout_token from Authorization header or request body
        logout_token = (
            request.META.get('HTTP_AUTHORIZATION', '').replace(
                'Bearer ', '',
            )
            or request.data.get('logout_token', '')
        )

        # Process logout asynchronously
        process_okta_logout.delay(
            logout_token=logout_token,
            request_data=slz.validated_data,
        )

        return self.response_ok()
