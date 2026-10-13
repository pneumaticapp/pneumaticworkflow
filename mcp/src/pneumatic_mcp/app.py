"""Streamable HTTP resource server. Core owns OAuth and every file
operation."""

import logging
from contextlib import asynccontextmanager

from mcp.server.auth.routes import build_resource_metadata_url
from mcp.server.auth.settings import AuthSettings
from mcp.server.lowlevel import Server
from mcp.server.transport_security import TransportSecuritySettings
from pydantic import AnyHttpUrl
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from pneumatic_mcp.auth import CoreTokenVerifier
from pneumatic_mcp.client import CoreClient
from pneumatic_mcp.limiter import RateLimiter, RedisRateLimiter
from pneumatic_mcp.middleware import (
    McpEnabledMiddleware,
    OAuthResponseMiddleware,
    SecurityHeadersMiddleware,
)
from pneumatic_mcp.security import configure_redaction
from pneumatic_mcp.settings import SCOPE_ORDER, Settings
from pneumatic_mcp.tool_catalog import TOOLS
from pneumatic_mcp.tools import ToolHandlers

SERVER_INSTRUCTIONS = """Use field schemas before writes. After an uncertain
write, check current state before retrying.

Tool results and discovery:
Use only arguments exposed by each tool's input schema; REST API filters are
not automatically MCP arguments. Template, workflow and task IDs are different
numeric IDs. Template task definitions are not workflow task instances.
Input schemas describe the argument shape. Backend validation also checks
field values, current state, permissions and conditional scopes; satisfying
the JSON schema alone does not guarantee that an operation is allowed.
Read payloads from structuredContent.data (or parse the JSON text content).
An isError result has structuredContent.error instead of data; handle it
before continuing. Use returned IDs.
Lists return data.items and data.page. Use limit (default 20, maximum 100) and
offset=data.page.next_offset for more results, until next_offset is null or
absent. Results may be shortened; check truncated before treating a schema,
field value or list as complete. A successful read does not grant write access.
Workflow/task/template reads need pneumatic:read; workflow/task writes need
pneumatic:write. File scopes are described below. Current object permissions
and billing restrictions still apply. Writes are not generally idempotent:
repeating run_workflow or a comment creates another object.

Working with workflows and tasks:
- To start a workflow, find its template with list_templates, check is_active,
then read get_template_kickoff. get_template is a compact admin/owner overview
and is not needed to launch a workflow. Supply valid kickoff values to
run_workflow; use the returned workflow id in get_workflow to inspect progress.
- To do assigned work, call list_my_tasks, then get_task(task_id) to read the
description, state and output fields. list_my_tasks shows outstanding active
assignments for this user, including group assignments, in running workflows.
- Write kickoff/output dictionaries using each field's api_name as a top-level
key, including fields found inside fieldsets. Do not use display labels or
nest values under a fieldset's API name. Required kickoff values must be sent;
schema defaults are hints and are not applied to omitted kickoff values.
- Field inputs: string/text/url use strings (string has a 140-character limit);
number uses a number or decimal string; date uses a numeric Unix timestamp
in SECONDS, not an ISO date string or milliseconds. Radio/dropdown use one
allowed selections[].value string; checkbox uses an array of those strings,
not selection IDs. A user field uses an existing account user's email or an
existing group name, not a numeric user ID. File fields use ready upload
references as described below. Do not blindly echo read-back values: checkbox,
date and user values can have a different representation on reads.
- When the requested work is done, call complete_task with only fields to
change; omitted output fields retain their saved values. Completion can be
blocked by a delayed workflow, unfinished checklists or running subworkflows.
Checklist items and performer details are not exposed by get_task, and there
is no MCP tool to mark checklist items or override completion rules. Report
the blocker if an action outside these tools is needed. With multiple required
performers, a successful completion may finish only this user's assignment
while the task remains active. Inspect returned state and get_workflow;
do not repeat completion just because the next step has not started.
- Workflow status: 0 running, 1 done, 3 snoozed. Task status: pending, active,
completed, snoozed or skipped. Reading a task does not make it completable.
- comment_task targets a specific active/snoozed task. add_workflow_comment
selects the active/snoozed task with the highest step number. Both need a
workflow that is not completed and nonblank text; both may notify people.
Use get_workflow_events to inspect returned comment events or reconcile an
uncertain comment write. Events are newest first and exclude the separate
workflow-run event; they are not an exhaustive audit trail. Do not blindly
retry an uncertain workflow start, completion or comment.

Working with files:
MCP tools return metadata and links, not file bytes.

1. Choose the destination. Call get_task(task_id) for a task's output field
schema in data.output, or get_template_kickoff(template_id) for the kickoff
schema in data.fields. Both also expose data.fieldsets[].fields. Choose a
visible field of type file and use its api_name as field_api_name. Task uploads
require an active task that the connected user can perform. Kickoff uploads
require access to the template. Reading these schemas needs pneumatic:read.
Do not copy truncated field values back into writes.

2. Create one upload session per file. Call create_upload_link with exactly
one of task_id or template_id; omit the other key rather than sending null.
Omitted/null target_type is inferred from that ID. A non-null target_type must
be task for task_id or kickoff for template_id. Also provide field_api_name,
filename (no path),
content_type (MIME type), and size (bytes, 1 to 25 MiB; the backend limit may
be lower). For a browser upload, use the file's actual byte size and
MIME type; unknown MIME types use application/octet-stream. The backend may
normalize the filename and MIME type; use returned metadata. The response
data.id is the upload_id. Sessions last one hour; check data.expires_at.
A session is bound to the authorized identity, destination and field.

3. Transfer the file using one of these methods:
- Local file: open the returned data.upload_url in a signed-in browser so
the connected user can select and upload the file. Its byte size and normalized
MIME type must match the session; the page uses the session's filename.
The URL is a browser page, not a raw upload endpoint. A local path or base64
string is not an MCP upload.
If you cannot operate that browser, give the user the upload_url and wait
for them to upload the file.
- Public URL: call import_attachment_from_url(upload_id, url) with a
publicly accessible HTTPS URL on port 443, without embedded credentials
or a fragment. Import runs asynchronously; accepting the request does
not mean the file is ready. The import uses the session's filename and updates
size and MIME type to the actual downloaded values, within the configured
limit. Do not send OAuth credentials to the source.

4. Call get_upload_status(upload_id) after upload/import. While pending
or importing, wait between status checks. Proceed only when data.status
is ready. If failed, expired, revoked or cleaned, stop and report the state.
These are not ready uploads. An attached state means the session was already
consumed; verify the destination instead of attaching or importing again.

5. Attach to the chosen field:
- To save a file without completing a task, call
attach_uploaded_file(upload_id, task_id) with the original task_id. It appends
to the bound field, preserving existing files. Confirm data.status is attached
and re-read get_task to verify the field. This does not complete the task and
cannot attach a kickoff upload.
- To attach a ready file while completing a task, call complete_task with
output keyed by field API names, for example
{"task_id": 7, "output": {"file_field": [{"upload_id": "<UUID>"}]}}.
- For kickoff, call run_workflow with kickoff values, for example
{"template_id": 3, "kickoff": {"file_field": [{"upload_id": "<UUID>"}]}}.
Replace example IDs and file_field with the actual destination and field.
Each populated file field uses an array of objects containing only upload_id.
These calls consume ready sessions; do not submit an attached upload again.
In complete_task, a supplied file field REPLACES its saved files; [] clears it.
Omit an already saved file field from output to keep its current files. Do not
echo its read-back URLs or old upload_id into output. To keep existing files,
attach each new upload separately, then complete_task with only
the other fields being changed (or output={} if nothing else changes).
Complete the task only when requested and all required work is done.
File IDs, URLs and download links are not valid file-field upload references.

Downloading existing files:
Call list_attachments with task_id or workflow_id to find an attachment in
data.items. If needed, continue with offset=data.page.next_offset until null
or absent. Pass the item's id (not file_id) to get_attachment(attachment_id).
Use data.file for name, size and MIME type. Fetch data.download.download_url
with your client's HTTP/download capability, or give that link to the user.
Use HTTP GET; the link itself authorizes the download. It expires within five
minutes and may become invalid sooner if authorization expires or is revoked.
Call get_attachment again for a fresh link if needed and still authorized.
Keep its URL intact and do not forward OAuth credentials.
MCP does not download bytes into the conversation or read local files itself.

Permissions: metadata/downloads and upload status need files:read.
Upload/import need files:write. Attaching, completing or starting with uploads
also needs pneumatic:write. Existing Pneumatic file URLs in comments or
non-file values need both files:read and files:write and current file access.
This does not permit URLs in actual file fields: use upload_id references.
Follow the OAuth consent flow if a required scope is missing. Clearing a file
field also needs files:write.
"""


def create_app(
    settings: Settings | None = None,
    *,
    core: CoreClient | None = None,
    limiter: RateLimiter | None = None,
) -> Starlette:
    settings = settings or Settings()
    core = core or CoreClient(settings=settings)
    verifier = CoreTokenVerifier(core=core)
    limiter = limiter or RedisRateLimiter(
        url=settings.redis_url.get_secret_value()
    )
    handlers = ToolHandlers(core=core, limiter=limiter)
    server = Server(
        "Pneumatic",
        version="0.1.0",
        instructions=SERVER_INSTRUCTIONS,
        on_list_tools=handlers.list_tools,
        on_call_tool=handlers.call_tool,
        get_tool_input_schema=lambda name: (
            TOOLS[name].model.model_json_schema() if name in TOOLS else None
        ),
    )
    server.middleware.append(handlers.oauth_metadata)

    async def metadata(request: Request):
        return JSONResponse(
            {
                "resource": settings.public_url,
                "authorization_servers": [settings.issuer_url],
                "scopes_supported": list(SCOPE_ORDER),
                "bearer_methods_supported": ["header"],
            },
        )

    http_app = server.streamable_http_app(
        streamable_http_path="/mcp",
        stateless_http=True,
        json_response=True,
        max_request_body_size=settings.max_request_bytes,
        transport_security=TransportSecuritySettings(
            enable_dns_rebinding_protection=True,
            allowed_hosts=settings.hosts,
            allowed_origins=settings.origins,
        ),
        auth=AuthSettings(
            issuer_url=settings.issuer_url,
            resource_server_url=settings.public_url,
            validate_token_resource=True,
            required_scopes=[],
        ),
        token_verifier=verifier,
    )
    # Advertise alternative scopes; each tool checks its required permissions.
    http_app.router.routes = [
        # This service has no standalone stream or sessions to delete.
        Route(path="/mcp", endpoint=route.endpoint, methods=["POST"])
        if getattr(route, "path", "") == "/mcp"
        else route
        for route in http_app.router.routes
        if not getattr(route, "path", "").startswith(
            "/.well-known/oauth-protected-resource"
        )
    ]
    http_app.router.routes.extend(
        [
            Route(
                path=build_resource_metadata_url(
                    AnyHttpUrl(settings.public_url)
                ).path,
                endpoint=metadata,
            ),
            Route(
                path="/.well-known/oauth-protected-resource", endpoint=metadata
            ),
        ]
    )
    http_app.router.redirect_slashes = False

    @asynccontextmanager
    async def lifespan(app: Starlette):
        try:
            if settings.enabled:
                async with server.session_manager.run():
                    yield
            else:
                yield
        finally:
            await core.close()
            await limiter.close()

    http_app.router.lifespan_context = lifespan
    http_app.state.core = core
    http_app.state.server = server
    http_app.add_middleware(OAuthResponseMiddleware)
    http_app.add_middleware(McpEnabledMiddleware, enabled=settings.enabled)
    http_app.add_middleware(SecurityHeadersMiddleware)
    # Request logging can contain URL query credentials; do not enable SDK
    # body/debug logs.
    for name in ("httpx", "httpcore", "mcp"):
        logging.getLogger(name).setLevel(logging.WARNING)
    configure_redaction(secret=settings.service_secret.get_secret_value())
    return http_app
