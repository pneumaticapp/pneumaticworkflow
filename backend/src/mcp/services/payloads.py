from collections.abc import Callable
from typing import Any

from django.contrib.auth import get_user_model
from rest_framework.exceptions import PermissionDenied

from src.authentication.exceptions import (
    InsufficientScope,
)
from src.mcp import messages
from src.mcp.constants import (
    UPLOAD_REFERENCE_KEY,
)
from src.mcp.enums import (
    McpScope,
)
from src.storage.enums import (
    UploadTargetType,
)
from src.mcp.models import Delegation, UploadSession
from src.processes.models.templates.template import Template
from src.processes.models.workflows.task import Task
from src.storage.services.attachments import AttachmentService
from src.storage.services.upload_sessions import UploadSessionService
from src.storage.utils import extract_file_ids_from_payload
from src.processes.services.upload_fields import UploadFieldService
from src.utils.validation import raise_validation_error

UserModel = get_user_model()


class McpPayloadService:
    """Replace upload references in delegated writes with file links.

    Requests without an MCP delegation pass through unchanged.
    """

    EMPTY_REFERENCES = (None, [], '')

    @classmethod
    def get_run_payload(
        cls,
        user: UserModel,
        delegation: Delegation | None,
        payload: Any,
        template: Template,
    ) -> Any:
        if not cls._is_mcp_payload(
            delegation=delegation,
            payload=payload,
        ):
            return payload
        cls.check_write_files(
            user=user,
            delegation=delegation,
            payload=payload,
        )
        kickoff = payload.get('kickoff') or {}
        if not isinstance(kickoff, dict):
            return payload
        fields = UploadFieldService.get_kickoff_file_fields(
            template=template,
        )
        return {
            **payload,
            'kickoff': UploadFieldService.map_file_values(
                value=kickoff,
                names=set(fields),
                transform=lambda name, value: cls._get_kickoff_links(
                    user=user,
                    delegation=delegation,
                    template_id=template.pk,
                    field_id=fields[name].pk,
                    references=value,
                ),
            ),
        }

    @classmethod
    def get_complete_payload(
        cls,
        user: UserModel,
        delegation: Delegation | None,
        payload: Any,
        task: Task,
    ) -> Any:
        if not cls._is_mcp_payload(
            delegation=delegation,
            payload=payload,
        ):
            return payload
        cls.check_write_files(
            user=user,
            delegation=delegation,
            payload=payload,
        )
        cls.check_complete_file_scopes(
            delegation=delegation,
            payload=payload,
            task=task,
        )
        output = payload.get('output')
        if not isinstance(output, dict):
            return payload
        names = UploadFieldService.get_task_file_names(task=task)
        return {
            **payload,
            'output': UploadFieldService.map_file_values(
                value=output,
                names=names,
                transform=lambda name, value: cls._get_output_links(
                    user=user,
                    delegation=delegation,
                    task_id=task.pk,
                    field_name=name,
                    references=value,
                ),
            ),
        }

    @classmethod
    def check_complete_file_scopes(
        cls,
        delegation: Delegation | None,
        payload: Any,
        task: Task,
    ):
        """Writing a field that holds files needs the file write scope."""
        if not isinstance(payload, dict):
            return
        names = UploadFieldService.get_task_linked_file_names(task=task)
        if UploadFieldService.contains_fields(
            value=payload.get('output'),
            names=names,
        ):
            cls.require_file_scopes(
                delegation=delegation,
                scopes={McpScope.FILE_WRITE},
            )

    @classmethod
    def check_write_files(
        cls,
        user: UserModel,
        delegation: Delegation | None,
        payload: Any,
    ):
        """Existing file links may be reused only by a reader of the file."""
        if not cls._is_mcp_payload(
            delegation=delegation,
            payload=payload,
        ):
            return
        file_ids = extract_file_ids_from_payload(value=payload)
        if not file_ids:
            return
        cls.require_file_scopes(
            delegation=delegation,
            scopes={McpScope.FILE_READ, McpScope.FILE_WRITE},
        )
        service = AttachmentService(user=user)
        if not service.check_account_files_permission(file_ids=file_ids):
            raise PermissionDenied

    @classmethod
    def require_file_scopes(
        cls,
        delegation: Delegation | None,
        scopes: set[str],
    ):
        """Check the delegated file scopes."""
        if not {McpScope.WRITE, *scopes} <= set(delegation.scopes):
            raise InsufficientScope(
                required_scopes=[McpScope.WRITE, *sorted(scopes)],
            )

    @classmethod
    def _is_mcp_payload(
        cls,
        delegation: Delegation | None,
        payload: Any,
    ) -> bool:
        return isinstance(delegation, Delegation) and isinstance(
            payload,
            dict,
        )

    @classmethod
    def _get_kickoff_links(
        cls,
        user: UserModel,
        delegation: Delegation,
        template_id: int,
        field_id: int,
        references: Any,
    ) -> Any:
        if references in (None, []):
            return references
        cls.require_file_scopes(
            delegation=delegation,
            scopes={McpScope.FILE_WRITE},
        )
        return cls._get_reference_links(
            user=user,
            delegation=delegation,
            references=references,
            is_target=lambda session: (
                session.target_type == UploadTargetType.KICKOFF
                and session.template_id == template_id
                and session.field_template_id == field_id
            ),
        )

    @classmethod
    def _get_output_links(
        cls,
        user: UserModel,
        delegation: Delegation,
        task_id: int,
        field_name: str,
        references: Any,
    ) -> Any:
        cls.require_file_scopes(
            delegation=delegation,
            scopes={McpScope.FILE_WRITE},
        )
        if references in cls.EMPTY_REFERENCES:
            return references
        return cls._get_reference_links(
            user=user,
            delegation=delegation,
            references=references,
            is_target=lambda session: (
                session.target_type == UploadTargetType.TASK
                and session.task_id == task_id
                and session.field_api_name == field_name
            ),
        )

    @classmethod
    def _get_reference_links(
        cls,
        user: UserModel,
        delegation: Delegation | None,
        references: Any,
        is_target: Callable[[UploadSession], bool],
    ) -> list[str]:
        """Consume ready uploads bound to the field and return links."""
        if not isinstance(references, list):
            raise_validation_error(message=messages.MSG_MCP_0015)
        links = []
        for reference in references:
            if not isinstance(reference, dict) or set(reference) != {
                UPLOAD_REFERENCE_KEY,
            }:
                raise_validation_error(message=messages.MSG_MCP_0016)
            links.append(UploadSessionService.consume(
                user=user,
                delegation=delegation,
                session_id=reference[UPLOAD_REFERENCE_KEY],
                is_target=is_target,
            ))
        return links
