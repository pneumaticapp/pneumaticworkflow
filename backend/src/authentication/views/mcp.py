from typing import Any

from django.conf import settings
from django.http import Http404, HttpRequest
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView

from src.authentication.services.mcp_auth import (
    LoginTokenAuthentication,
    ServiceAuthentication,
)
from src.generics.responses import set_private_headers


class EnabledMixin:
    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any):
        if not settings.MCP_ENABLED:
            raise Http404
        return set_private_headers(
            super().dispatch(request, *args, **kwargs),
        )


class PrivateServiceView(EnabledMixin, APIView):
    authentication_classes = (ServiceAuthentication,)
    permission_classes = (AllowAny,)


class UserView(EnabledMixin, APIView):
    authentication_classes = (LoginTokenAuthentication,)
    permission_classes = (IsAuthenticated,)
