"""Bounded structured output schemas for MCP tools."""

from pydantic import BaseModel, ConfigDict, Field, JsonValue

MAX_RESULT_BYTES = 64 * 1024


MAX_NESTED_ITEMS = 100


class Output(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Envelope[T](Output):
    data: T
    truncated: bool = False


class Template(Output):
    id: int
    name: str
    description: str | None = None
    is_active: bool | None = None


class Selection(Output):
    id: int | None = None
    api_name: str | None = None
    value: JsonValue = None


class FieldSchema(Output):
    api_name: str
    name: str | None = None
    type: str | int | None = None
    is_required: bool | None = None
    is_hidden: bool | None = None
    description: str | None = None
    default: JsonValue = None
    value: JsonValue = None
    selections: list[Selection] = Field(default_factory=list)


class Fieldset(Output):
    api_name: str
    name: str | None = None
    fields: list[FieldSchema] = Field(default_factory=list)


class TemplateTask(Output):
    api_name: str | None = None
    name: str | None = None
    number: int | None = None


class TemplateDetail(Output):
    id: int
    name: str
    description: str | None = None
    is_active: bool | None = None
    tasks: list[TemplateTask] = Field(default_factory=list)
    kickoff: list[FieldSchema] = Field(default_factory=list)
    kickoff_fieldsets: list[Fieldset] = Field(default_factory=list)


class Kickoff(Output):
    template_id: int
    name: str | None = None
    fields: list[FieldSchema]
    fieldsets: list[Fieldset] = Field(default_factory=list)


class Workflow(Output):
    id: int
    name: str
    status: str | int | None = None
    template_id: int | None = None
    is_urgent: bool | None = None
    due_date_tsp: float | None = None


class Task(Output):
    id: int
    name: str
    status: str | int | None = None
    workflow_id: int | None = None
    is_completed: bool | None = None
    due_date_tsp: float | None = None


class WorkflowDetail(Workflow):
    description: str | None = None
    tasks: list[Task] = Field(default_factory=list)
    kickoff: list[FieldSchema] = Field(default_factory=list)
    kickoff_fieldsets: list[Fieldset] = Field(default_factory=list)


class TaskDetail(Task):
    description: str | None = None
    output: list[FieldSchema] = Field(default_factory=list)
    fieldsets: list[Fieldset] = Field(default_factory=list)


class Event(Output):
    id: int
    type: str | int | None = None
    text: str | None = None
    created_tsp: float | None = None
    task_id: int | None = None
    workflow_id: int | None = None


class Attachment(Output):
    id: int
    file_id: str
    access_type: str | int | None = None
    source_type: str | int | None = None


class FileMetadata(Output):
    file_id: str
    name: str
    size: int = Field(ge=0)
    content_type: str


class Download(Output):
    download_url: str
    expires_at: str
    expires_in: int = Field(gt=0, le=300)


class AttachmentDetail(Output):
    attachment: Attachment
    file: FileMetadata
    download: Download


class Upload(Output):
    id: str
    status: str
    task_id: int | None = None
    template_id: int | None = None
    field_api_name: str | None = None
    filename: str | None = None
    content_type: str | None = None
    size: int | None = None
    expires_at: str | None = None
    upload_url: str | None = None
    file_id: str | None = None


class Pagination(Output):
    limit: int
    offset: int
    returned: int
    next_offset: int | None = None
    total: int | None = None


class Page[T](Output):
    items: list[T]
    page: Pagination
