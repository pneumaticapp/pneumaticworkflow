from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from src.authentication.services.mcp_auth import DelegationAuthentication
from src.authentication.views.mcp import EnabledMixin
from src.mcp.permissions import McpBillingPermission


class BusinessView(EnabledMixin, APIView):
    authentication_classes = (DelegationAuthentication,)
    permission_classes = (IsAuthenticated, McpBillingPermission)
