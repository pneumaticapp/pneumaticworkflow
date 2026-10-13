from rest_framework.request import Request
from rest_framework.views import APIView

from src.accounts.permissions import AccountBillingPermission
from src.mcp.models import Delegation


def is_delegated_auth(auth: object) -> bool:
    """MCP billing and account filters apply only to a delegation."""
    return isinstance(auth, Delegation)


class McpBillingPermission(AccountBillingPermission):
    """Apply billing restrictions to delegated MCP requests only."""

    def has_permission(self, request: Request, view: APIView) -> bool:
        if not is_delegated_auth(auth=request.auth):
            return True
        return super().has_permission(request=request, view=view)
