from src.processes.services.upload_fields import UploadFieldService
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework.request import Request
from rest_framework.response import Response

from src.mcp.serializers.templates import KickoffResponseSerializer
from src.mcp.views.base import BusinessView


@extend_schema(tags=['MCP'], responses={200: OpenApiTypes.OBJECT})
class KickoffView(BusinessView):
    def get(self, request: Request, template_id: int):
        template = UploadFieldService.get_kickoff_template(
            user=request.user,
            template_id=template_id,
        )
        return Response(KickoffResponseSerializer(template).data)
