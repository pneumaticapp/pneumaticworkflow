from uuid import UUID

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework.request import Request
from rest_framework.response import Response

from src.authentication.serializers import ConnectionSerializer
from src.authentication.services.connections import ConnectionService
from src.authentication.views.mcp import (
    UserView,
)


@extend_schema(tags=['MCP'], responses={200: OpenApiTypes.OBJECT})
class ConnectionsView(UserView):
    def get(self, request: Request):
        return Response(
            {
                'results': ConnectionSerializer(
                    ConnectionService.get_user_connections(user=request.user),
                    many=True,
                ).data,
            },
        )


@extend_schema(tags=['MCP'], responses={204: None})
class ConnectionRevokeView(UserView):
    def delete(self, request: Request, connection_id: UUID):
        ConnectionService.revoke(
            connection=ConnectionService.get_user_connection(
                user=request.user,
                connection_id=connection_id,
            ),
        )
        return Response(status=204)
