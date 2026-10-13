from drf_spectacular.utils import extend_schema
from rest_framework.request import Request
from rest_framework.response import Response

from src.authentication.serializers import (
    DelegationResponseSerializer,
    DelegationSerializer,
    IntrospectionResponseSerializer,
    IntrospectionSerializer,
)
from src.authentication.services.delegation import DelegationService
from src.authentication.exceptions import (
    InvalidMcpToken,
)
from src.authentication.views.mcp import (
    PrivateServiceView,
)


@extend_schema(exclude=True)
class IntrospectionView(PrivateServiceView):
    def post(self, request: Request):
        serializer = IntrospectionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            binding = DelegationService.get_access_binding(
                **serializer.validated_data,
            )
        except InvalidMcpToken:
            return Response({'active': False})
        return Response(IntrospectionResponseSerializer(binding).data)


@extend_schema(exclude=True)
class DelegationView(PrivateServiceView):
    def post(self, request: Request):
        serializer = DelegationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        issued = DelegationService.create(**serializer.validated_data)
        return Response(DelegationResponseSerializer(issued).data)
