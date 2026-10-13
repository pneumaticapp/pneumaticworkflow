from uuid import UUID

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from src.authentication.services.mcp_auth import (
    DelegationAuthentication,
    LoginTokenAuthentication,
)
from src.accounts.permissions import (
    AccountBillingPermission,
)
from src.mcp.serializers.uploads import (
    AttachSerializer,
    ImportSerializer,
    UploadAttachedResponseSerializer,
    UploadCreateResponseSerializer,
    UploadSerializer,
    UploadSessionSerializer,
    UploadStateResponseSerializer,
    UploadTokenResponseSerializer,
)
from src.storage.services.upload_sessions import UploadSessionService
from src.mcp.views.base import (
    BusinessView,
)
from src.authentication.views.mcp import (
    EnabledMixin,
    UserView,
)


@extend_schema(
    tags=['MCP'],
    request=UploadSerializer,
    responses={201: OpenApiTypes.OBJECT},
)
class UploadCreateView(BusinessView):
    def post(self, request: Request):
        serializer = UploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        issued = UploadSessionService.create(
            user=request.user,
            delegation=request.auth,
            data=serializer.validated_data,
        )
        return Response(
            UploadCreateResponseSerializer(
                issued.session,
                context={'credential': issued.credential},
            ).data,
            status=201,
        )


@extend_schema(tags=['MCP'], responses={200: OpenApiTypes.OBJECT})
class UploadStatusView(EnabledMixin, APIView):
    authentication_classes = (
        DelegationAuthentication,
        LoginTokenAuthentication,
    )
    permission_classes = (IsAuthenticated, AccountBillingPermission)

    def get(self, request: Request, session_id: UUID):
        session = UploadSessionService.get_session(
            user=request.user,
            delegation=request.auth,
            session_id=session_id,
        )
        return Response(UploadSessionSerializer(session).data)


@extend_schema(
    tags=['MCP'],
    request=None,
    responses={200: OpenApiTypes.OBJECT},
)
class UploadTokenView(UserView):
    def post(self, request: Request, session_id: UUID):
        return Response(
            UploadTokenResponseSerializer(
                UploadSessionService.create_upload_token(
                    user=request.user,
                    delegation=request.auth,
                    session_id=session_id,
                ),
            ).data,
        )


@extend_schema(
    tags=['MCP'],
    request=ImportSerializer,
    responses={202: OpenApiTypes.OBJECT},
)
class UploadImportView(BusinessView):
    def post(self, request: Request, session_id: UUID):
        serializer = ImportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        session = UploadSessionService.queue_import(
            user=request.user,
            delegation=request.auth,
            session_id=session_id,
            url=serializer.validated_data['url'],
        )
        return Response(
            UploadStateResponseSerializer(session).data,
            status=202,
        )


@extend_schema(
    tags=['MCP'],
    request=AttachSerializer,
    responses={200: OpenApiTypes.OBJECT},
)
class UploadAttachView(BusinessView):
    def post(self, request: Request, session_id: UUID):
        serializer = AttachSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        session = UploadSessionService.attach(
            user=request.user,
            delegation=request.auth,
            session_id=session_id,
            task_id=serializer.validated_data['task_id'],
        )
        return Response(UploadAttachedResponseSerializer(session).data)
