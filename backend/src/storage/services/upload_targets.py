from rest_framework.exceptions import PermissionDenied

from src.authentication.services.connections import ConnectionService
from src.mcp.models import UploadSession
from src.storage.enums import UploadTargetType
from src.processes.services.upload_fields import UploadFieldService


class UploadTargetService:
    @classmethod
    def check_target(cls, session: UploadSession):
        """The connection and the bound field must still be writable."""
        ConnectionService.check_live(connection=session.connection)
        user = session.connection.user
        if session.target_type == UploadTargetType.TASK:
            _task, field = UploadFieldService.get_task_field(
                user=user,
                task_id=session.task_id,
                field_api_name=session.field_api_name,
            )
            is_same_field = field.pk == session.field_id
        else:
            _template, field = UploadFieldService.get_kickoff_field(
                user=user,
                template_id=session.template_id,
                field_api_name=session.field_api_name,
            )
            is_same_field = field.pk == session.field_template_id
        if not is_same_field:
            raise PermissionDenied
