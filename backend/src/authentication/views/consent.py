from django.http import HttpRequest, HttpResponseRedirect
from django.views import View
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework.request import Request
from rest_framework.response import Response

from src.authentication.responses import get_oauth_error_response
from src.authentication.serializers import (
    ConsentContextSerializer,
    ConsentSerializer,
    LoginCodeResponseSerializer,
    LoginCompleteSerializer,
    RequestSerializer,
)
from src.authentication.services.consent import ConsentService
from src.authentication.enums import (
    OAuthErrorCode,
)
from src.authentication.exceptions import (
    InvalidLoginCode,
)
from src.authentication.views.mcp import (
    EnabledMixin,
    UserView,
)


@extend_schema(
    tags=['MCP'],
    request=RequestSerializer,
    responses={200: OpenApiTypes.OBJECT},
)
class LoginCodeView(UserView):
    def post(self, request: Request):
        serializer = RequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        issued = ConsentService.create_login_code(
            user=request.user,
            **serializer.validated_data,
        )
        return Response(LoginCodeResponseSerializer(issued).data)


@extend_schema(
    tags=['MCP'],
    request=ConsentSerializer,
    responses={200: OpenApiTypes.OBJECT},
)
class ConsentView(UserView):
    def get(self, request: Request):
        serializer = RequestSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        context = ConsentService.get_context(
            user=request.user,
            **serializer.validated_data,
        )
        return Response(ConsentContextSerializer(context).data)

    def post(self, request: Request):
        serializer = ConsentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        issued = ConsentService.approve(
            user=request.user,
            **serializer.validated_data,
        )
        return Response(LoginCodeResponseSerializer(issued).data)


class LoginCompleteView(EnabledMixin, View):
    def get(self, request: HttpRequest):
        serializer = LoginCompleteSerializer(data=request.GET)
        if not serializer.is_valid():
            return get_oauth_error_response(
                error=OAuthErrorCode.INVALID_LOGIN_CODE,
            )
        try:
            redirect_url = ConsentService.complete_login(
                request=request,
                **serializer.validated_data,
            )
        except InvalidLoginCode:
            return get_oauth_error_response(
                error=OAuthErrorCode.INVALID_LOGIN_CODE,
            )
        return HttpResponseRedirect(redirect_url)
