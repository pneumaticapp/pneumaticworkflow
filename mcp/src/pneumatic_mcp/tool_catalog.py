"""Public tool contracts, OAuth requirements and operation bindings."""

from dataclasses import dataclass

import mcp_types as types
from pydantic import JsonValue

from pneumatic_mcp.outputs import (
    Attachment,
    AttachmentDetail,
    Envelope,
    Event,
    Kickoff,
    Output,
    Page,
    Task,
    TaskDetail,
    Template,
    TemplateDetail,
    Upload,
    Workflow,
    WorkflowDetail,
)
from pneumatic_mcp.settings import (
    FILES_READ_SCOPE,
    FILES_WRITE_SCOPE,
    READ_SCOPE,
    WRITE_SCOPE,
)
from pneumatic_mcp.tool_inputs import (
    AddWorkflowComment,
    Args,
    AttachmentArgs,
    AttachmentPage,
    AttachUploadedFile,
    CommentTask,
    CompleteTask,
    CreateUploadLink,
    ImportAttachment,
    PageArgs,
    RunWorkflow,
    TaskArgs,
    TemplateArgs,
    TemplatePage,
    UploadArgs,
    WorkflowArgs,
    WorkflowEvents,
    WorkflowPage,
)


class OAuthTool(types.Tool):
    security_schemes: list[dict[str, JsonValue]]


@dataclass(frozen=True)
class ToolSpec:
    name: str
    model: type[Args]
    description: str
    method: str
    path: str
    scopes: tuple[str, ...]
    output: type[Output]
    file_links: bool = False
    field_values: str | None = None

    @property
    def write(self) -> bool:
        return self.method != "GET"

    def schema(self) -> types.Tool:
        schemes = [{"type": "oauth2", "scopes": list(self.scopes)}]
        return OAuthTool(
            name=self.name,
            title=self.name.replace("_", " ").capitalize(),
            description=self.description,
            inputSchema=self.model.model_json_schema(),
            outputSchema=self.output.model_json_schema(),
            security_schemes=schemes,
            meta={"securitySchemes": schemes},
            annotations=types.ToolAnnotations(
                readOnlyHint=not self.write,
                destructiveHint=self.name == "complete_task",
                idempotentHint=not self.write,
                openWorldHint=self.name
                in {
                    "run_workflow",
                    "complete_task",
                    "import_attachment_from_url",
                },
            ),
        )


TOOL_SPECS = (
    ToolSpec(
        name="list_templates",
        scopes=(READ_SCOPE,),
        output=Envelope[Page[Template]],
        model=TemplatePage,
        description="List templates accessible to this connection.",
        method="GET",
        path="/templates",
    ),
    ToolSpec(
        name="get_template",
        scopes=(READ_SCOPE,),
        output=Envelope[TemplateDetail],
        model=TemplateArgs,
        description="Get an accessible template, its tasks and kickoff.",
        method="GET",
        path="/templates/{template_id}",
    ),
    ToolSpec(
        name="get_template_kickoff",
        scopes=(READ_SCOPE,),
        output=Envelope[Kickoff],
        model=TemplateArgs,
        description="Get the starter-visible kickoff field schema.",
        method="GET",
        path="/integrations/mcp/templates/{template_id}/kickoff",
    ),
    ToolSpec(
        name="list_workflows",
        scopes=(READ_SCOPE,),
        output=Envelope[Page[Workflow]],
        model=WorkflowPage,
        description="List workflows accessible to this connection.",
        method="GET",
        path="/workflows",
    ),
    ToolSpec(
        name="get_workflow",
        scopes=(READ_SCOPE,),
        output=Envelope[WorkflowDetail],
        model=WorkflowArgs,
        description="Get an accessible workflow and its current state.",
        method="GET",
        path="/workflows/{workflow_id}",
    ),
    ToolSpec(
        name="get_workflow_events",
        scopes=(READ_SCOPE,),
        output=Envelope[Page[Event]],
        model=WorkflowEvents,
        description="List events in an accessible workflow.",
        method="GET",
        path="/workflows/{workflow_id}/events",
    ),
    ToolSpec(
        name="list_my_tasks",
        scopes=(READ_SCOPE,),
        output=Envelope[Page[Task]],
        model=PageArgs,
        description="List tasks assigned to the connected user.",
        method="GET",
        path="/v3/tasks",
    ),
    ToolSpec(
        name="get_task",
        scopes=(READ_SCOPE,),
        output=Envelope[TaskDetail],
        model=TaskArgs,
        description="Get an accessible task and its output field schema.",
        method="GET",
        path="/v2/tasks/{task_id}",
    ),
    ToolSpec(
        name="run_workflow",
        scopes=(WRITE_SCOPE,),
        output=Envelope[WorkflowDetail],
        file_links=True,
        field_values="kickoff",
        model=RunWorkflow,
        description="Start a workflow using kickoff values. Kickoff "
        "upload references additionally "
        "require files:write. Workflow automation may notify people "
        "or trigger external integrations.",
        method="POST",
        path="/templates/{template_id}/run",
    ),
    ToolSpec(
        name="complete_task",
        scopes=(WRITE_SCOPE,),
        output=Envelope[TaskDetail],
        file_links=True,
        field_values="output",
        model=CompleteTask,
        description="Complete an assigned task and advance its workflow. "
        "This may notify people "
        "or trigger external integrations.",
        method="POST",
        path="/v2/tasks/{task_id}/complete",
    ),
    ToolSpec(
        name="add_workflow_comment",
        scopes=(WRITE_SCOPE,),
        output=Envelope[Event],
        file_links=True,
        model=AddWorkflowComment,
        description="Add a comment to an accessible workflow. References "
        "to Pneumatic file URLs "
        "additionally require files:read and files:write.",
        method="POST",
        path="/workflows/{workflow_id}/comment",
    ),
    ToolSpec(
        name="comment_task",
        scopes=(WRITE_SCOPE,),
        output=Envelope[Event],
        file_links=True,
        model=CommentTask,
        description="Add a comment to an accessible task. References "
        "to Pneumatic file URLs "
        "additionally require files:read and files:write.",
        method="POST",
        path="/v2/tasks/{task_id}/comment",
    ),
    ToolSpec(
        name="list_attachments",
        scopes=(FILES_READ_SCOPE,),
        output=Envelope[Page[Attachment]],
        model=AttachmentPage,
        description="List file metadata accessible to this connection.",
        method="GET",
        path="/attachments",
    ),
    ToolSpec(
        name="get_attachment",
        scopes=(FILES_READ_SCOPE,),
        output=Envelope[AttachmentDetail],
        model=AttachmentArgs,
        description="Get authorized file metadata and a download link.",
        method="GET",
        path="/integrations/mcp/attachments/{attachment_id}",
    ),
    ToolSpec(
        name="create_upload_link",
        scopes=(FILES_WRITE_SCOPE,),
        output=Envelope[Upload],
        model=CreateUploadLink,
        description="Create a task or template kickoff file upload "
        "session. Transfer bytes using "
        "the returned upload page.",
        method="POST",
        path="/integrations/mcp/uploads",
    ),
    ToolSpec(
        name="get_upload_status",
        scopes=(FILES_READ_SCOPE,),
        output=Envelope[Upload],
        model=UploadArgs,
        description="Get the state of an upload owned by this connection.",
        method="GET",
        path="/integrations/mcp/uploads/{upload_id}",
    ),
    ToolSpec(
        name="import_attachment_from_url",
        scopes=(FILES_WRITE_SCOPE,),
        output=Envelope[Upload],
        model=ImportAttachment,
        description="Request a storage import into an existing upload "
        "session; poll its status.",
        method="POST",
        path="/integrations/mcp/uploads/{upload_id}/import",
    ),
    ToolSpec(
        name="attach_uploaded_file",
        scopes=(WRITE_SCOPE, FILES_WRITE_SCOPE),
        output=Envelope[Upload],
        model=AttachUploadedFile,
        description="Attach a ready upload to its authorized task field "
        "through core validation.",
        method="POST",
        path="/integrations/mcp/uploads/{upload_id}/attach",
    ),
)


TOOLS = {spec.name: spec for spec in TOOL_SPECS}
