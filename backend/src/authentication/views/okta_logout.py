from rest_framework.views import APIView

from src.authentication.permissions import SSOPermission
from src.authentication.serializers import OktaLogoutSerializer
from src.authentication.services.okta_logout import OktaLogoutService
from src.generics.mixins.views import (
    AnonymousMixin,
    CustomViewSetMixin,
)


class OktaLogoutView(
    AnonymousMixin,
    CustomViewSetMixin,
    APIView,
):
    """View for handling Okta logout operations"""

    permission_classes = (SSOPermission,)

    def get_authenticators(self):
        """No authentication required for logout endpoint"""
        return []

    def post(self, request, *args, **kwargs):
        """Process Okta Global Token Revocation (GTR) request"""
        slz = OktaLogoutSerializer(data=request.data)
        if not slz.is_valid():
            return self.response_ok()
        service = OktaLogoutService()
        service.process_logout(**slz.validated_data)
        return self.response_ok()
