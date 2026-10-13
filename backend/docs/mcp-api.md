# Approved MCP backend API contract

## Shared backend ownership — 2026-10-13

MCP and ordinary REST permissions now share template-access and task-performer
queries in processes.permissions; the REST guest-task restriction is preserved.
Billing composition and non-HTTP billing checks live in accounts.permissions.
BaseInputSerializer lives in generics.serializers. Opaque credential helpers
and protocol authentication exceptions live in authentication; existing
PneumaticToken formats and validation remain unchanged.

Pure filename, MIME and file-ID helpers live in backend storage.file_metadata,
with shared storage constants/messages. The existing FileServiceClient owns
both user uploads and post_internal for MCP storage calls. The latter preserves
its private URL, service secret, timeout, proxy and redirect restrictions.
The unused replay target check is removed. MCP retains its operation/scope
allowlist, consent bindings, upload sessions/capabilities and durable imports.
Models and migration history are unchanged.


This document supersedes the initial draft. All paths omit a trailing slash.
OAuth uses django-oauth-toolkit **3.4.1**, authorization code + **S256 PKCE**, **DCR
and CIMD**. Access tokens expire after **900 seconds (15 minutes)**. Refresh tokens
rotate; reuse detection revokes the connection. OAuth tokens are MCP credentials,
not ordinary Pneumatic API credentials. Resource must exactly match MCP_PUBLIC_URL.
Issuer uses MCP_ISSUER_URL (public frontend origin), never the private backend URL.

## Configuration and authentication

- MCP_ENABLED=no: all MCP endpoints and credentials disabled by default.
- MCP_PUBLIC_URL=https://my.pneumatic.app/mcp: exact OAuth resource.
- MCP_ISSUER_URL=https://my.pneumatic.app: public OAuth issuer.
- MCP_SERVICE_SECRET: private MCP endpoints use X-MCP-Service-Secret header.
- MCP_FILE_SERVICE_SECRET: storage callbacks use Authorization: Bearer <secret>.
- Configure distinct secrets of at least 32 characters, the HTTPS public resource
  ending exactly /mcp, its matching HTTPS issuer origin, the internal storage URL,
  and an import cap from 1 to 26214400 during production setup. Backend startup
  does not validate these settings.
- THROTTLE_14=10/min, THROTTLE_15=60/min, THROTTLE_16=120/min: existing backend
  throttle scopes for registration, shared authorize/login, and shared token/revoke.
  These rates enforce minimum intervals, using the default backend cache.
- MCP_MAX_IMPORT_BYTES=26214400: maximum 25 MiB.
- Existing FILE_SERVICE_URL is the public frontend /files URL. Core server calls use ONLY MCP_FILE_SERVICE_URL=http://file-service:8000.
- Existing FRONTEND_URL builds frontend /mcp/connect and /files/upload links.
- MCP_BACKEND_URL=http://pneumatic-nginx is consumed by service/storage.
- MCP_REDIS_URL is available for service coordination; core state is PostgreSQL.

DCR and CIMD are enabled when MCP_ENABLED=yes. Four scopes: pneumatic:read, pneumatic:write, files:read, files:write. Default pneumatic:read.
DCR/CIMD clients have can_introspect=False. Only authenticated private MCP service
introspection is exposed. No password, implicit or client-credentials user grants.

## OAuth endpoints

| Method/path | Input | Response |
|---|---|---|
| GET /oauth/mcp/authorize | client_id,redirect_uri,response_type=code,scope,state,code_challenge,code_challenge_method=S256,resource=MCP_PUBLIC_URL | 302 FRONTEND_URL/mcp/connect?request_id=UUID; invalid OAuth request 400 |
| POST /oauth/mcp/token | OAuth form authorization_code/code/redirect_uri/client_id/code_verifier/resource or refresh_token/refresh_token/client_id/resource; registered confidential client authentication supported | 200 access_token,token_type=Bearer,expires_in=900,refresh_token,scope; invalid grant 400/client 401 |
| POST /oauth/mcp/register | RFC7591 JSON redirect_uris,client_name,grant_types=[authorization_code,refresh_token],response_types=[code],token_endpoint_auth_method=none or client_secret_basic | 201 registered metadata, confidential secret once; invalid metadata 400 |
| POST /oauth/mcp/revoke | RFC7009 form token,token_type_hint,client_id/client authentication | 200, owned connection/access/refresh/delegations revoked immediately |
| GET /oauth/mcp/login | code and request_id=UUID | consumes one-time bound code, HttpOnly session, then 302 /mcp/connect?request_id=UUID&step=consent; final consent handoff redirects to registered OAuth client; invalid/expired/reused code 400 |
| GET /.well-known/oauth-authorization-server | none | issuer,authorization_endpoint,token_endpoint,registration_endpoint,revocation_endpoint,scopes_supported,code_challenge_methods_supported=[S256],client_id_metadata_document_supported=true |
| GET /.well-known/oauth-protected-resource[/mcp] | none | resource=MCP_PUBLIC_URL,authorization_servers=[MCP_ISSUER_URL],scopes_supported |

CIMD uses HTTPS URL client IDs and Toolkit's validated, SSRF-protected metadata
fetcher. Toolkit validates exact registered redirect URIs and PKCE. Consent always
runs for a fresh authorization request; client skip_authorization cannot bypass it.

## Frontend bridge

Express converts its existing cookie token to Authorization: Bearer <login token>
server-side and enforces same-origin CSRF on mutations. Core does not read Express
cookies. API keys/guest/public/OAuth/delegated tokens cannot manage connections.

| Method/path | Input | Response |
|---|---|---|
| GET /integrations/mcp/consent | user Bearer, query request_id=UUID | 200 {request_id,client:{id,name},client_id,client_name,account:{id,name},user_id,account_id,scopes:[...],expires_at,login_complete}; foreign/unknown 404, expired/consumed 410 |
| POST /integrations/mcp/login-code | user Bearer, JSON {request_id:UUID} | 200 {code,request_id,expires_in:60}; user/account/request bound; one use |
| POST /integrations/mcp/consent | user Bearer, JSON {request_id:UUID,allow:boolean} | 200 {code,request_id,expires_in:60}; completed bridge required; frontend navigates fixed /oauth/mcp/login?code&request_id, core performs final OAuth registered-client redirect with code or access_denied/state |
| GET /integrations/mcp/connections | user Bearer | 200 {results:[{id,client_id,client_name,scopes,created_at,revoked_at,user_id,account_id}]}; newest first, current user/account only |
| DELETE /integrations/mcp/connections/{uuid} | user Bearer | 204, repeat 204, foreign 404 |

## Private MCP service

Header X-MCP-Service-Secret. Invalid/missing authentication 401; disabled MCP 404.
Service authentication failure body is
`{detail:"Invalid MCP service credentials.",code:"service_auth_failed"}`.
An authenticated service's invalid source token at delegate returns 401
`{detail:"Invalid MCP access token.",code:"invalid_token"}`.

- POST /internal/mcp/introspect JSON {token,resource}: 200 {active:false} or
  {active:true,user_id,account_id,client_id,connection_id,scope,aud:[MCP_PUBLIC_URL],exp}.
  scope is space-delimited, aud is exactly [MCP_PUBLIC_URL], exp Unix seconds.
- POST /internal/mcp/delegate JSON {token,resource,tool,method,path,scopes?}:
  200 {credential:mcp-d_...,token_type:Bearer,expires_in:60,expires_at:UNIX,operation,scopes:[...],connection_id,user_id,account_id,
  audience:pneumatic-backend|pneumatic-files}. Optional scopes narrows the grant.
  Source token is never persisted in raw form. Invalid source 401, route/scope 403.

Business calls use ONLY Authorization: Bearer mcp-d_.... Every call checks live
connection, source token, user status/is_active/deletion, account membership and
account deletion, client, scope, audience, exact method/path/tool. Any unlisted
endpoint/action is denied, including views overriding their authentication.
Repeated consent for the same active user/account/client/resource reuses the
connection and unions consented scopes. Each source access token retains its own
strict scope set. Revoked grants get a new connection. Legacy live duplicate rows
retain durable upload identities and revoke together;
cross-user/account/client/resource reuse is denied.

Delegated REST calls retain the existing `AuthTokenType.API` behavior, including
template API integration tracking. Audit events use the existing backend request context and payload format.

## Operation map

| tool | method/path | scope |
|---|---|---|
| list_templates | GET /templates | pneumatic:read |
| get_template | GET /templates/{id} | pneumatic:read |
| get_template_kickoff | GET /integrations/mcp/templates/{id}/kickoff | pneumatic:read |
| list_workflows | GET /workflows | pneumatic:read |
| get_workflow | GET /workflows/{id} | pneumatic:read |
| get_workflow_events | GET /workflows/{id}/events | pneumatic:read |
| list_my_tasks | GET /v3/tasks | pneumatic:read |
| get_task | GET /v2/tasks/{id} | pneumatic:read |
| list_attachments | GET /attachments | files:read |
| get_attachment | GET /integrations/mcp/attachments/{id} | files:read |
| run_workflow | POST /templates/{id}/run | pneumatic:write |
| complete_task | POST /v2/tasks/{id}/complete | pneumatic:write |
| add_workflow_comment | POST /workflows/{id}/comment | pneumatic:write |
| comment_task | POST /v2/tasks/{id}/comment | pneumatic:write |
| create_upload_link | POST /integrations/mcp/uploads | files:write |
| get_upload_status | GET /integrations/mcp/uploads/{uuid} | files:read |
| import_attachment_from_url | POST /integrations/mcp/uploads/{uuid}/import | files:write |
| attach_uploaded_file | POST /integrations/mcp/uploads/{uuid}/attach | pneumatic:write + files:write |
| get_file_metadata | GET storage /mcp/files/{file_id} | files:read |
| create_download_ticket | POST storage /mcp/files/{file_id}/download-ticket | files:read |

Last two operations use pneumatic-files; others pneumatic-backend. Existing REST
operations keep existing payloads/permissions. Kickoff schema is starter-safe
using run permission. Attachment retrieval checks existing object permission.
`list_attachments` supports optional integer `task_id`, `workflow_id`, `limit`
and `offset` query parameters. Target filters and file permissions apply before
pagination/counting; MCP lists are restricted to the current account and billing.

Writes use the existing backend endpoints and their transaction behavior. No
Idempotency-Key is required and successful responses are not cached. Repeating
run_workflow or a comment creates another object. After an uncertain outcome,
inspect current state before retrying. Each call checks current access and scopes.

## Upload sessions

Sessions belong to connection/user/account/task OR template kickoff/file field,
expire after 1h, cap
25 MiB (configuration may lower this cap). Status
pending/importing/ready/attached/failed/cleaned/expired/revoked. Unsafe names
are rejected; accepted filenames are normalized with storage's Unicode-preserving
secure_filename algorithm. Unknown/executable MIME types become
application/octet-stream. Browser never submits arbitrary file IDs or completion.

- POST /integrations/mcp/uploads delegated create_upload_link, JSON
  {target_type:task|kickoff,task_id?|template_id?,field_api_name,filename,
  content_type,size}: 201 (exactly one target ID)
  {id,status,expires_at,user_id,account_id,connection_id,target_type,task_id,
  template_id,field_api_name,
  filename,content_type,size,max_size,upload_url,credential}. credential=mcp-u_....
  upload_url is FRONTEND_URL/mcp/uploads/{id} (browser form). Capability is narrow and lasts 300s.
- GET /integrations/mcp/uploads/{uuid}, user Bearer or get_upload_status:
  200 session metadata above without credential, plus file_id and error.
  User/account/connection ownership checked, foreign 404.
- POST /integrations/mcp/uploads/{uuid}/token user Bearer: 200
  {access_token:mcp-u_...,token_type:Bearer,expires_in:300,upload_session_id,
  file_upload_url}. file_upload_url is FRONTEND_URL/files/upload. Browser keeps token ephemeral and POSTs existing /files/upload
  with Bearer capability plus X-MCP-Upload-Session: UUID.
- POST /integrations/mcp/uploads/{uuid}/import delegated import_attachment_from_url,
  JSON {url}: 202 {id,status:importing}. Core durable Celery job
  calls storage after commit, retries use same session identity.
- POST /integrations/mcp/uploads/{uuid}/attach delegated attach_uploaded_file,
  JSON {task_id}: 200 {id,status:attached,task_id,field_api_name,
  file_id}. Verified storage completion required. Permissions rechecked;
  field updated using existing TaskFieldService and attachment permission services.

Celery calls storage POST /internal/mcp/import, Authorization: Bearer
MCP_FILE_SERVICE_SECRET, JSON {credential,upload_session_id,url,filename}.
Core persists an ImportJob outbox in PostgreSQL before ack and dispatches/recover pending jobs through Celery. Storage owns bounded safe fetching and durable file-session deduplication.
There are at most TWO active import leases per account across all core workers.
Claims serialize under a PostgreSQL account row lock and count only running jobs
whose 90-second lease remains live. Capacity-limited jobs stay queued, defer
30 seconds and consume no attempt. HTTP timeout is 75 seconds; Celery import task
soft/hard limits are 80/85 seconds (prefork worker), before the lease expires.
The periodic dispatcher recovers expired leases through the same claim path.
Core owns authorization, durable scheduling, callback verification and attachment. No scanner is claimed. PostgreSQL holds connection/user/account/scopes and credential hashes so all instances recheck the same revocation state.

## Storage callbacks

Header X-MCP-File-Service-Secret: MCP_FILE_SERVICE_SECRET (Bearer secret also
accepted for storage interoperability). All callbacks accept JSON.

- POST /internal/mcp/validate-files:
  {credential?,operation:upload|import|download|metadata,upload_session_id?,file_id?,
  connection_id?,authorization_id?} -> 200 {active:false} or
  {active:true,user_id,account_id,connection_id,operation,upload_session_id?,
  authorization_id?,expires_at?}. Upload/import need mcp-u_... and
  matching session. Metadata/download initially need mcp-d_..., matching audience,
  file/path and permission. Download-ticket revalidation may omit credential and
  send connection_id/file_id/authorization_id (ALL required). Initial metadata
  and download responses return authorization_id UUID and expires_at Unix seconds.
  Core binds that row to the original access token, file and connection; expiry is
  min(source token expiry, now+300s). Every ticket/Range request rechecks the row,
  original AccessBinding/token expiry/resource/scopes, live client/user/account,
  billing and existing attachment permission. Missing/mismatched IDs deny.
  Legacy metadata/ticket IDs preserve the original flat identity, including
  Unicode, spaces and parentheses, up to 512 characters. JSON file_id is RAW and
  is never filename-normalized or trimmed. The bound delegated URL segment is
  canonical UTF-8 percent encoding, `quote(file_id,safe='')`, decoded once and
  checked by exact re-encoding. Slashes/backslashes, query/fragment/percent chars,
  Unicode controls/line separators and exact dot segments are rejected. Interior
  double dots remain valid. Noncanonical/double-encoded paths deny. Delegated
  paths permit 8192 characters to accommodate 512-character Unicode IDs.
- POST /internal/mcp/complete-upload:
  {credential,upload_session_id,file_id,name,size,content_type} -> 200
  {id,status:ready,file_id}. Matching upload/import capability and live grant
  required; identical ready repeat accepted to reconcile lost callbacks; mismatched
  file/metadata or consumed session 409; invalid credential 403.
  Browser uploads require exact requested name/size/MIME. URL imports retain the
  requested filename and accept trusted storage's actual valid MIME and actual
  size <= MCP_MAX_IMPORT_BYTES, then persist actual metadata.
- POST /internal/mcp/cleanup-upload:
  {upload_session_id,file_id,account_id,user_id} -> 200 {eligible:boolean}.
  Under connection/session locks, exact identity, expired session, created >=24h
  ago, never attached, no Attachment references (including deleted), and no queued
  or running ImportJob are required. An eligible session becomes terminal cleaned;
  if completion was lost and core has no file_id, only storage's deterministic
  UUID5(NAMESPACE_URL, "pneumatic:mcp:{session_uuid}") is eligible and is persisted
  before authorization. This fences further completion/attachment.
  identical retries remain eligible. Core hourly Celery cleanup_uploads calls
  storage POST /internal/mcp/cleanup {limit:100} with the file service secret.

Notifications and webhooks use the existing Celery tasks and retry behavior.
Event notifications and file ACL synchronization are scheduled with ordinary
transaction.on_commit callbacks. URL import jobs retain their own persisted
state, retry schedule and attempt/lease fencing.

Kickoff sessions use target_type=kickoff plus template_id (exactly one target ID).
Task sessions use target_type=task plus task_id. run_workflow keeps its existing
kickoff mapping, but each populated file field MUST be a list of objects
[{upload_id: UUID}, ...], e.g. {kickoff:{field_file:[{upload_id:UUID}]}}.
Core checks the current user's connection, template, file field, ready status,
expiry and files:write before mapping to verified storage links and consuming the
sessions in the same workflow transaction. Raw file IDs/URLs are rejected.

`complete_task` uses the same reference shape in `output`, including nested
fieldsets. Every included actual FILE field requires `files:write`, including
null/empty-list/empty-string clears; omitted FILE fields retain existing values.
Provided TEXT/STRING/URL fields containing an old file-service link also require
`files:write` to remove that link, even when the replacement is plain text or
empty. Removal alone does not require `files:read`.
Any actual configured file-service markdown or plain URL in run/complete/comment
payloads, including TEXT/STRING/URL fields, requires BOTH `files:read` and
`files:write`, current account ownership and current attachment permission.
External links remain ordinary text. Missing conditional file scopes return 403
`{code:"insufficient_scope",required_scopes:[...],detail:"..."}`; the MCP service
uses this exact scope list for step-up. Object permission failures remain 403
without `insufficient_scope`. Each request checks current permissions.

## Retention and telemetry

Celery beat dispatches imports every 30 seconds, prunes expired ephemeral state
every 60 seconds, and asks storage for a bounded cleanup batch every hour. The
pruner selects at most 500 indexed expired rows per model: Delegation, LoginCode,
CodeBinding, AuthorizationRequest, UploadCapability and FileAuthorization. Live
rows and pending ImportJobs are retained.
Verified completion and terminal failure/cleanup erase signed source URLs; the
pruner also clears any older terminal sessions' residual source URL.

OAuth access/refresh family maintenance is deliberately delegated to DOT's
official `cleartokens` command and its retention settings. Do not schedule it
until the refresh-family/reuse-evidence retention has been reviewed; the MCP
pruner never deletes these bindings or OAuth token family evidence.

WSGI, ASGI and Celery Sentry hooks redact MCP credentials, codes, cookies, headers,
request bodies/query strings, signed URL queries, download tickets, breadcrumbs
and spans. MCP exception frame locals are removed entirely. Ordinary event
diagnostics are preserved outside the MCP credential boundary. Private storage
requests disable environment proxies and redirect following; only
MCP_FILE_SERVICE_SECRET is sent to storage.
