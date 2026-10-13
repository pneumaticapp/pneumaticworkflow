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
        description="List template summaries visible to the connected user. "
        "Use optional search to find a template and its numeric id. "
        "Check is_active before starting a workflow; use "
        "get_template_kickoff to read its launch fields. Supports pagination.",
        method="GET",
        path="/templates",
    ),
    ToolSpec(
        name="get_template",
        scopes=(READ_SCOPE,),
        output=Envelope[TemplateDetail],
        model=TemplateArgs,
        description="Get a compact template overview, task definitions and "
        "kickoff fields. Requires account-owner access or an admin who owns "
        "the template. To prepare a launch with starter/viewer access, use "
        "get_template_kickoff instead. Template task definitions are not "
        "workflow task instances and cannot be passed to complete_task.",
        method="GET",
        path="/templates/{template_id}",
    ),
    ToolSpec(
        name="get_template_kickoff",
        scopes=(READ_SCOPE,),
        output=Envelope[Kickoff],
        model=TemplateArgs,
        description="Get the kickoff schema under template-access permissions "
        "without requiring template edit permission. Inspect data.fields and "
        "data.fieldsets[].fields for API names, types, required/hidden flags "
        "and choices before run_workflow. Reading a schema does not launch "
        "a workflow or guarantee the template is active.",
        method="GET",
        path="/integrations/mcp/templates/{template_id}/kickoff",
    ),
    ToolSpec(
        name="list_workflows",
        scopes=(READ_SCOPE,),
        output=Envelope[Page[Workflow]],
        model=WorkflowPage,
        description="List workflow summaries visible to the connected user, "
        "optionally filtered by template_id. Supports pagination. Use "
        "get_workflow with a returned workflow id for task instances and "
        "kickoff values; this list does not return full task details.",
        method="GET",
        path="/workflows",
    ),
    ToolSpec(
        name="get_workflow",
        scopes=(READ_SCOPE,),
        output=Envelope[WorkflowDetail],
        model=WorkflowArgs,
        description="Get workflow state, kickoff values and compact task "
        "instances (excluding skipped tasks). Workflow status is numeric: "
        "0 running, 1 done, 3 snoozed. Inspect task statuses to find current "
        "work; call get_task for its output field schema. Check truncated "
        "before treating returned details as complete. "
        "Reading a workflow does not grant permission to complete its tasks.",
        method="GET",
        path="/workflows/{workflow_id}",
    ),
    ToolSpec(
        name="get_workflow_events",
        scopes=(READ_SCOPE,),
        output=Envelope[Page[Event]],
        model=WorkflowEvents,
        description="List workflow events and comments, newest first, with "
        "pagination. The separate workflow-run event is excluded; this is "
        "not an exhaustive audit log. Use it to inspect progress or reconcile "
        "an uncertain comment write before retrying.",
        method="GET",
        path="/workflows/{workflow_id}/events",
    ),
    ToolSpec(
        name="list_my_tasks",
        scopes=(READ_SCOPE,),
        output=Envelope[Page[Task]],
        model=PageArgs,
        description="List active, unfinished assignments for the connected "
        "user, including group assignments, in running workflows. Supports "
        "pagination. This tool does not expose completed-task or other-user "
        "filters. Call get_task with a returned id before working on it.",
        method="GET",
        path="/v3/tasks",
    ),
    ToolSpec(
        name="get_task",
        scopes=(READ_SCOPE,),
        output=Envelope[TaskDetail],
        model=TaskArgs,
        description="Get task state, description, current output values and "
        "field schemas in data.output and data.fieldsets[].fields. Task "
        "status is pending, active, completed, snoozed or skipped. Read this "
        "before complete_task; use field API names, not labels. Read access "
        "alone does not grant completion permission. Checklist items and "
        "performer details are not included in this compact response.",
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
        description="Create and start a new workflow from an active template "
        "using kickoff values. Read get_template_kickoff first and supply "
        "required fields by API name; defaults are not automatically applied "
        "to omitted kickoff fields. Returns the new workflow and its task "
        "instances. Ready kickoff upload references also require files:write. "
        "May notify people or trigger integrations. Repeating the call "
        "creates another workflow; after an uncertain result, check current "
        "workflows before retrying.",
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
        description="Submit completion for the connected user on an active "
        "task. Read get_task first; output changes only supplied fields. "
        "Delayed/completed workflows, unfinished checklists or running "
        "subworkflows can block completion. With multiple required performers "
        "the task can remain active after this user's completion: inspect "
        "the returned task and get_workflow before claiming advancement. "
        "May notify people or trigger integrations. Do not blindly retry "
        "after an uncertain result.",
        method="POST",
        path="/v2/tasks/{task_id}/complete",
    ),
    ToolSpec(
        name="add_workflow_comment",
        scopes=(WRITE_SCOPE,),
        output=Envelope[Event],
        file_links=True,
        model=AddWorkflowComment,
        description="Add a nonblank comment to a workflow that is not "
        "completed. The backend associates it with the active or snoozed "
        "task having the highest step number; use comment_task to target a "
        "specific eligible task. Returns a comment event and may notify "
        "people. Repeating the call creates another comment. Pneumatic file "
        "URLs require files:read and files:write and current file access.",
        method="POST",
        path="/workflows/{workflow_id}/comment",
    ),
    ToolSpec(
        name="comment_task",
        scopes=(WRITE_SCOPE,),
        output=Envelope[Event],
        file_links=True,
        model=CommentTask,
        description="Add a nonblank comment to the specified active or "
        "snoozed task in a workflow that is not completed, subject to comment "
        "permissions. Returns a comment event; it does not complete the task "
        "and may notify people. Repeating the call creates another comment. "
        "Pneumatic file URLs also require files:read and files:write and "
        "current file access.",
        method="POST",
        path="/v2/tasks/{task_id}/comment",
    ),
    ToolSpec(
        name="list_attachments",
        scopes=(FILES_READ_SCOPE,),
        output=Envelope[Page[Attachment]],
        model=AttachmentPage,
        description="List accessible attachment records with id and file_id, "
        "optionally filtered by task_id and/or workflow_id, with pagination. "
        "This list does not include filenames, sizes or download links; use "
        "get_attachment with the attachment id for those details.",
        method="GET",
        path="/attachments",
    ),
    ToolSpec(
        name="get_attachment",
        scopes=(FILES_READ_SCOPE,),
        output=Envelope[AttachmentDetail],
        model=AttachmentArgs,
        description="Get an attachment by its numeric attachment_id (not "
        "file_id). Returns data.file metadata and a temporary "
        "data.download.download_url for HTTP GET. No file bytes are returned; "
        "the link lasts at most five minutes and remains subject to current "
        "authorization. Call again for a fresh link if needed.",
        method="GET",
        path="/integrations/mcp/attachments/{attachment_id}",
    ),
    ToolSpec(
        name="create_upload_link",
        scopes=(FILES_WRITE_SCOPE,),
        output=Envelope[Upload],
        model=CreateUploadLink,
        description="Create a file upload session bound to a task or template "
        "kickoff field; this call does not transfer bytes. Supply exactly one "
        "destination ID. The returned data.id is upload_id; use the browser "
        "page in data.upload_url or import_attachment_from_url to transfer "
        "the file, then poll get_upload_status until ready before attaching.",
        method="POST",
        path="/integrations/mcp/uploads",
    ),
    ToolSpec(
        name="get_upload_status",
        scopes=(FILES_READ_SCOPE,),
        output=Envelope[Upload],
        model=UploadArgs,
        description="Get an upload session's metadata and current status "
        "under the same authorized identity. Only ready sessions can be "
        "attached. Pending/importing means wait; attached means already "
        "consumed; failed/expired/revoked/cleaned is not ready. This read "
        "does not transfer or attach a file.",
        method="GET",
        path="/integrations/mcp/uploads/{upload_id}",
    ),
    ToolSpec(
        name="import_attachment_from_url",
        scopes=(FILES_WRITE_SCOPE,),
        output=Envelope[Upload],
        model=ImportAttachment,
        description="Start an asynchronous import from a public HTTPS URL "
        "into an existing pending upload session. This does not create a "
        "session or attach a file. Use create_upload_link first, then poll "
        "get_upload_status until ready. The response acknowledges the import "
        "request, not completion; do not repeat it while importing.",
        method="POST",
        path="/integrations/mcp/uploads/{upload_id}/import",
    ),
    ToolSpec(
        name="attach_uploaded_file",
        scopes=(WRITE_SCOPE, FILES_WRITE_SCOPE),
        output=Envelope[Upload],
        model=AttachUploadedFile,
        description="Append a ready, unexpired task upload to the file field "
        "bound when its session was created. task_id must match that "
        "session's task; existing files are preserved. Returns status "
        "attached and consumes the session. Does not complete the task and "
        "cannot attach a kickoff upload; do not reuse an attached upload_id.",
        method="POST",
        path="/integrations/mcp/uploads/{upload_id}/attach",
    ),
)


TOOLS = {spec.name: spec for spec in TOOL_SPECS}
