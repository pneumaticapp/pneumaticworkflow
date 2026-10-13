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
    offset: int = Field(default=0, ge=0, le=1_000_000)


class TemplatePage(PageArgs):
    search: str | None = Field(default=None, max_length=200)


class TemplateArgs(Args):
    template_id: ObjectId


class WorkflowPage(PageArgs):
    template_id: ObjectId | None = None


class WorkflowArgs(Args):
    workflow_id: ObjectId


class WorkflowEvents(PageArgs):
    workflow_id: ObjectId


class TaskArgs(Args):
    task_id: ObjectId


class AttachmentPage(PageArgs):
    workflow_id: ObjectId | None = None
    task_id: ObjectId | None = None


class AttachmentArgs(Args):
    attachment_id: ObjectId


class RunWorkflow(Args):
    template_id: ObjectId
    kickoff: dict[str, JsonValue] = Field(
        default_factory=dict,
        description="Values keyed by kickoff field API names. File fields"
        " use arrays of "
        "{upload_id: UUID} references to ready kickoff "
        "uploads and require files:write. "
        "References to existing Pneumatic file URLs require "
        "files:read and files:write.",
    )
    name: str | None = Field(default=None, min_length=1, max_length=200)
    is_urgent: bool = False


class CompleteTask(Args):
    task_id: ObjectId
    output: dict[str, JsonValue] = Field(
        default_factory=dict,
        description="Values keyed by task output field API names. File "
        "fields use arrays of "
        "{upload_id: UUID} references to ready task uploads "
        "and require files:write. "
        "Clearing file fields also requires files:write. "
        "References to existing "
        "Pneumatic file URLs require files:read and files:write.",
    )


class AddWorkflowComment(Args):
    workflow_id: ObjectId
    text: str = Field(min_length=1, max_length=10000)


class CommentTask(Args):
    task_id: ObjectId
    text: str = Field(min_length=1, max_length=10000)


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
    target_type: Literal["task", "kickoff"] | None = None
    task_id: ObjectId | None = None
    template_id: ObjectId | None = None
    field_api_name: str = Field(
        min_length=1, max_length=200, pattern=r"^[A-Za-z0-9_-]+$"
    )
    filename: str = Field(min_length=1, max_length=255)
    content_type: str = Field(
        min_length=3, max_length=200, pattern=r"^[\w.+-]+/[\w.+-]+$"
    )
    size: int = Field(ge=1, le=25 * 1024 * 1024)

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
        min_length=36, max_length=36, description="Upload session UUID."
    )

    @field_validator("upload_id")
    @classmethod
    def valid_uuid(cls, value: str) -> str:
        return str(UUID(hex=value))


class ImportAttachment(UploadArgs):
    url: str = Field(
        min_length=1, max_length=2048, description="Public HTTPS source URL."
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
    task_id: ObjectId
