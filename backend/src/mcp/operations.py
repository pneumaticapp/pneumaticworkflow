import re
from dataclasses import dataclass
from typing import Optional

from src.mcp.constants import (
    FILE_SERVICE_FILES_PATH,
)
from src.mcp.enums import HttpMethod, McpAudience, McpScope, McpTool
from src.storage.file_metadata import decode_file_segment


@dataclass(frozen=True)
class Operation:
    method: str
    path: str
    scope: str
    audience: str = McpAudience.BACKEND
    extra_scopes: tuple[str, ...] = ()

    @property
    def required_scopes(self) -> set[str]:
        return {self.scope, *self.extra_scopes}


ID = r'[1-9][0-9]*'
UUID = r'[0-9a-fA-F-]{36}'
OPERATIONS = {
    McpTool.LIST_TEMPLATES: Operation(
        method=HttpMethod.GET,
        path=r'/templates',
        scope=McpScope.READ,
    ),
    McpTool.GET_TEMPLATE: Operation(
        method=HttpMethod.GET,
        path=rf'/templates/{ID}',
        scope=McpScope.READ,
    ),
    McpTool.GET_TEMPLATE_KICKOFF: Operation(
        method=HttpMethod.GET,
        path=rf'/integrations/mcp/templates/{ID}/kickoff',
        scope=McpScope.READ,
    ),
    McpTool.LIST_WORKFLOWS: Operation(
        method=HttpMethod.GET,
        path=r'/workflows',
        scope=McpScope.READ,
    ),
    McpTool.GET_WORKFLOW: Operation(
        method=HttpMethod.GET,
        path=rf'/workflows/{ID}',
        scope=McpScope.READ,
    ),
    McpTool.GET_WORKFLOW_EVENTS: Operation(
        method=HttpMethod.GET,
        path=rf'/workflows/{ID}/events',
        scope=McpScope.READ,
    ),
    McpTool.LIST_MY_TASKS: Operation(
        method=HttpMethod.GET,
        path=r'/v3/tasks',
        scope=McpScope.READ,
    ),
    McpTool.GET_TASK: Operation(
        method=HttpMethod.GET,
        path=rf'/v2/tasks/{ID}',
        scope=McpScope.READ,
    ),
    McpTool.LIST_ATTACHMENTS: Operation(
        method=HttpMethod.GET,
        path=r'/attachments',
        scope=McpScope.FILE_READ,
    ),
    McpTool.GET_ATTACHMENT: Operation(
        method=HttpMethod.GET,
        path=rf'/integrations/mcp/attachments/{ID}',
        scope=McpScope.FILE_READ,
    ),
    McpTool.RUN_WORKFLOW: Operation(
        method=HttpMethod.POST,
        path=rf'/templates/{ID}/run',
        scope=McpScope.WRITE,
    ),
    McpTool.COMPLETE_TASK: Operation(
        method=HttpMethod.POST,
        path=rf'/v2/tasks/{ID}/complete',
        scope=McpScope.WRITE,
    ),
    McpTool.COMMENT_TASK: Operation(
        method=HttpMethod.POST,
        path=rf'/v2/tasks/{ID}/comment',
        scope=McpScope.WRITE,
    ),
    McpTool.ADD_WORKFLOW_COMMENT: Operation(
        method=HttpMethod.POST,
        path=rf'/workflows/{ID}/comment',
        scope=McpScope.WRITE,
    ),
    McpTool.CREATE_UPLOAD_LINK: Operation(
        method=HttpMethod.POST,
        path=r'/integrations/mcp/uploads',
        scope=McpScope.FILE_WRITE,
    ),
    McpTool.GET_UPLOAD_STATUS: Operation(
        method=HttpMethod.GET,
        path=rf'/integrations/mcp/uploads/{UUID}',
        scope=McpScope.FILE_READ,
    ),
    McpTool.IMPORT_ATTACHMENT_FROM_URL: Operation(
        method=HttpMethod.POST,
        path=rf'/integrations/mcp/uploads/{UUID}/import',
        scope=McpScope.FILE_WRITE,
    ),
    McpTool.ATTACH_UPLOADED_FILE: Operation(
        method=HttpMethod.POST,
        path=rf'/integrations/mcp/uploads/{UUID}/attach',
        scope=McpScope.WRITE,
        extra_scopes=(McpScope.FILE_WRITE,),
    ),
    McpTool.GET_FILE_METADATA: Operation(
        method=HttpMethod.GET,
        path=r'/mcp/files/[^/]+',
        scope=McpScope.FILE_READ,
        audience=McpAudience.FILES,
    ),
    McpTool.CREATE_DOWNLOAD_TICKET: Operation(
        method=HttpMethod.POST,
        path=r'/mcp/files/[^/]+/download-ticket',
        scope=McpScope.FILE_READ,
        audience=McpAudience.FILES,
    ),
}


def get_operation(tool: str, method: str, path: str) -> Optional[Operation]:
    """Find the operation allowed for the request or None."""
    operation = OPERATIONS.get(tool)
    if (
        operation is None
        or method != operation.method
        or not re.fullmatch(operation.path, path)
    ):
        return None
    if tool in McpTool.FILE_SERVICE_TOOLS and not _is_valid_file_path(
        path=path,
    ):
        return None
    return operation


def _is_valid_file_path(path: str) -> bool:
    segment = path.removeprefix(FILE_SERVICE_FILES_PATH).split('/')[0]
    return decode_file_segment(value=segment) is not None
