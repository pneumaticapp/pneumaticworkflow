"""Validated arguments for the public MCP tools."""

from typing import Annotated, Literal
from urllib.parse import urlsplit
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    JsonValue,
    field_validator,
    model_validator,
)

ObjectId = Annotated[int, Field(gt=0, le=2**63 - 1)]


class Args(BaseModel):
    model_config = ConfigDict(
        extra="forbid", strict=True, hide_input_in_errors=True
    )


class PageArgs(Args):
    limit: int = Field(
        default=20, ge=1, le=100, description="Number of objects, maximum 100."
    )
    offset: int = Field(
        default=0,
        ge=0,
        le=1_000_000,
        description="Number of results to skip; use data.page.next_offset.",
    )


class TemplatePage(PageArgs):
    search: str | None = Field(
        default=None,
        max_length=200,
        description="Optional search text; omit for no search filter. "
        "Pagination still applies.",
    )


class TemplateArgs(Args):
    template_id: ObjectId = Field(
        description="Template ID from list_templates, not a workflow ID."
    )


class WorkflowPage(PageArgs):
    template_id: ObjectId | None = Field(
        default=None, description="Filter workflows by their template ID."
    )


class WorkflowArgs(Args):
    workflow_id: ObjectId = Field(
        description="Numeric workflow instance ID, not its template ID."
    )


class WorkflowEvents(PageArgs):
    workflow_id: ObjectId = Field(
        description="Numeric workflow instance ID whose events to list."
    )


class TaskArgs(Args):
    task_id: ObjectId = Field(
        description="Numeric workflow task instance ID, not a template step."
    )


class AttachmentPage(PageArgs):
    workflow_id: ObjectId | None = Field(
        default=None, description="Optional workflow attachment filter."
    )
    task_id: ObjectId | None = Field(
        default=None, description="Optional task attachment filter."
    )


class AttachmentArgs(Args):
    attachment_id: ObjectId = Field(
        description="Numeric attachment id from list_attachments, not file_id."
    )


class RunWorkflow(Args):
    template_id: ObjectId = Field(
        description="ID of the active template to start a new workflow from."
    )
    kickoff: dict[str, JsonValue] = Field(
        default_factory=dict,
        description="Values keyed by kickoff field API names, including "
        "fields inside fieldsets at the same top level. Read "
        "get_template_kickoff first; supply required values explicitly. "
        "Omitted fields do not automatically use their schema defaults. "
        "Populated file fields accept arrays of {upload_id: UUID} objects "
        "with no extra keys, referencing ready kickoff "
        "uploads and require files:write. "
        "Existing Pneumatic file links in non-file values require "
        "files:read and files:write; URLs are not valid file-field inputs.",
    )
    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
        description="Optional name for the new workflow.",
    )
    is_urgent: bool = Field(
        default=False, description="Whether to mark the new workflow urgent."
    )


class CompleteTask(Args):
    task_id: ObjectId = Field(
        description="ID of the active workflow task to submit completion for."
    )
    output: dict[str, JsonValue] = Field(
        default_factory=dict,
        description="Only the fields to change, keyed by task output field "
        "API names, including fieldset fields at the same top level. Omitted "
        "fields retain saved values; {} changes no fields. Read get_task "
        "first; read-back values are not always valid write inputs. Populated "
        "file fields accept arrays of {upload_id: UUID} objects with no "
        "extra keys, referencing ready task uploads "
        "and require files:write. "
        "Supplying a file field replaces its saved files; [] clears it. "
        "Clearing file fields also requires files:write. "
        "Existing Pneumatic file links in non-file values require "
        "files:read and files:write; URLs are not valid file-field inputs.",
    )


class AddWorkflowComment(Args):
    workflow_id: ObjectId = Field(
        description="Workflow ID; the backend selects its eligible task."
    )
    text: str = Field(
        min_length=1,
        max_length=10000,
        description="Nonblank comment text; supports Markdown.",
    )


class CommentTask(Args):
    task_id: ObjectId = Field(
        description="ID of the active or snoozed workflow task to comment on."
    )
    text: str = Field(
        min_length=1,
        max_length=10000,
        description="Nonblank comment text; supports Markdown.",
    )


class CreateUploadLink(Args):
    model_config = ConfigDict(
        extra="forbid",
        strict=True,
        hide_input_in_errors=True,
        json_schema_extra={
            "oneOf": [
                {
                    "required": ["task_id"],
                    "properties": {"task_id": {"type": "integer"}},
                    "not": {"required": ["template_id"]},
                },
                {
                    "required": ["template_id"],
                    "properties": {"template_id": {"type": "integer"}},
                    "not": {"required": ["task_id"]},
                },
            ]
        },
    )
    target_type: Literal["task", "kickoff"] | None = Field(
        default=None,
        description="Omitted/null means inferred from the destination ID. "
        "Non-null must be task for task_id or kickoff for template_id.",
    )
    task_id: ObjectId | None = Field(
        default=None,
        description="Destination task ID; supply this OR template_id, "
        "and omit the other key.",
    )
    template_id: ObjectId | None = Field(
        default=None,
        description="Destination template ID for a kickoff field; supply "
        "this OR task_id, and omit the other key.",
    )
    field_api_name: str = Field(
        min_length=1,
        max_length=200,
        pattern=r"^[A-Za-z0-9_-]+$",
        description="Exact api_name of the destination's visible file field.",
    )
    filename: str = Field(
        min_length=1,
        max_length=255,
        description="Filename without path separators, NUL, CR or LF; "
        "cannot equal '.' or '..'. Backend may normalize the name.",
    )
    content_type: str = Field(
        min_length=3,
        max_length=200,
        pattern=r"^[\w.+-]+/[\w.+-]+$",
        description="File MIME type; backend normalizes unknown types to "
        "application/octet-stream.",
    )
    size: int = Field(
        ge=1,
        le=25 * 1024 * 1024,
        description="Size in bytes, at most 25 MiB and the backend limit. "
        "Must match a browser upload; URL imports use their actual size.",
    )

    @model_validator(mode="after")
    def one_target(self):
        if (self.task_id is None) == (self.template_id is None):
            raise ValueError("Provide exactly one of task_id or template_id")
        expected = "task" if self.task_id is not None else "kickoff"
        if self.target_type is not None and self.target_type != expected:
            raise ValueError("target_type does not match the target ID")
        self.target_type = expected
        return self

    @field_validator("filename")
    @classmethod
    def safe_filename(cls, value: str) -> str:
        if any(
            char in value for char in ("/", "\\", "\x00", "\r", "\n")
        ) or value in {".", ".."}:
            raise ValueError(
                "Expected a filename without path separators "
                "or control characters"
            )
        return value


class UploadArgs(Args):
    # String validates consistently from SDK's decoded JSON under strict model
    # validation.
    upload_id: str = Field(
        min_length=36,
        max_length=36,
        description="Upload session UUID returned as data.id by "
        "create_upload_link; not a file_id or attachment ID.",
    )

    @field_validator("upload_id")
    @classmethod
    def valid_uuid(cls, value: str) -> str:
        return str(UUID(hex=value))


class ImportAttachment(UploadArgs):
    url: str = Field(
        min_length=1,
        max_length=2048,
        description="Public HTTPS source URL, port 443, without embedded "
        "credentials, a fragment, spaces or control characters.",
    )

    @field_validator("url")
    @classmethod
    def source_url(cls, value: str) -> str:
        parts = urlsplit(value)
        if (
            parts.scheme != "https"
            or not parts.hostname
            or parts.port not in (None, 443)
            or parts.username
            or parts.password
            or parts.fragment
            or any(ord(char) < 33 for char in value)
        ):
            raise ValueError(
                "Expected a public HTTPS URL without credentials or fragment"
            )
        # DNS, redirects, IP filtering, scanning and streaming limits belong to
        # storage.
        return value


class AttachUploadedFile(UploadArgs):
    task_id: ObjectId = Field(
        description="Original destination task ID of this upload session."
    )
