# Pneumatic MCP

## Delivery scope

An isolated Streamable HTTP resource server at `MCP_PUBLIC_URL` (normally
`https://my.pneumatic.app/mcp`). The existing Django backend owns OAuth,
connections and permissions. The existing file service owns
file bytes, metadata and bounded HTTPS imports. No new user database or
copy of workflow business logic is introduced.

Implementation stages: OAuth and read tools; write tools;
uploads/downloads/imports; integration validation and deployment packaging.
Every stage includes tests and correctness/security review. Confirmed defects
are fixed and rechecked; deployment and external-client evidence are reported
separately from passing local tests.

## Security boundaries

* OAuth authorization code with S256 PKCE, CIMD and compatible DCR,
  resource binding, issuer identification, refresh rotation/reuse protection.
* Access tokens last 15 minutes; refresh sessions expire after 30 inactive days.
* A connection binds client, user, account and consented scopes. Scope expansion
  for the same client/user/account/resource preserves the connection and existing
  uploads. Changing user, tenant or client creates a separate connection.
* External OAuth tokens are sent only to the authorization server for
  verification. Business endpoints receive a different opaque delegation.
* Delegations last at most 60 seconds and never longer than their source token.
  They bind source token, connection, user, tenant, audience, operation and
  scopes. Only hashes are retained. Every downstream request checks revocation
  and current permissions; failed validation never falls through to session auth.
* `pneumatic:read` and `pneumatic:write` cover workflow operations;
  `files:read` and `files:write` cover attachments. Attaching a file requires
  both write scopes and the normal task/field permission.
* Service-client authentication authorizes introspection/delegation, never
  impersonation of an arbitrary caller-supplied user. Dynamically registered
  OAuth clients cannot introspect other tokens.
* Secrets, source URLs, OAuth codes and download tickets are excluded from logs.

## Public routing

The frontend host routes exactly `/mcp` to the resource server; `/mcp/connect`,
`/mcp/connections` and `/mcp/uploads/...` remain frontend pages. OAuth lives under
`/oauth/mcp/`, leaving existing Google/Microsoft/SSO callbacks intact.
Well-known authorization/resource metadata is routed to Django. `/files/`
continues to route to the file service. API contracts live in
`backend/docs/mcp-api.md`; actual method/path/schema interoperability is covered
by contract tests.

The optional Compose `mcp` profile does not prevent nginx from starting when
disabled: its upstream is resolved at request time. `start.sh` derives the
profile from `MCP_ENABLED`. All services enforce the disabled state. Railway
sets `MCP_HOST` and the existing backend/file-service private hosts.

## Tools and side effects

Read tools: list_templates, get_template_kickoff, list_workflows, get_workflow,
get_workflow_events, list_my_tasks, get_task, list_attachments, get_attachment,
get_upload_status. Explicit pagination defaults to 20, maximum 100.

Write tools: run_workflow, complete_task, add_workflow_comment,
create_upload_link, import_attachment_from_url, attach_uploaded_file.
No deletion, forced workflow completion or administrative operations.
Tools expose input/output schemas and accurate read/write/destructive hints.
Authenticated clients discover all tools and their OAuth requirements; each call
enforces its scopes, and missing scopes trigger an explicit consent step.
No binary file bodies are embedded in tool results.

State-changing tools use the existing backend write behavior. They do not
require idempotency keys or cache successful responses. Repeated calls can
create another object. Check current state after an uncertain network outcome
before retrying. Notifications use the existing Celery tasks and callbacks;
URL imports retain their own durable job state.

## File lifecycle

Uploads use hour-long sessions bound to the consenting user/account/connection.
The logged-in browser uploads with a restricted credential to the existing file
service. Only a trusted storage acknowledgement marks the session uploaded.
The agent polls get_upload_status and attaches the resulting file to a task's
file field without completing the task. Kickoff attachments are passed to
run_workflow. Client-provided arbitrary file IDs are not upload confirmations.

Download tickets last at most five minutes and never outlive their source OAuth
authorization, permit only their specific file and GET/
Range operation, and recheck connection/current file permissions at each request.
Replies use `no-store` and `no-referrer`; ticket paths are redacted in proxy logs.

URL import is durable asynchronous work. It accepts HTTPS port 443, no credentials,
and allows at most two active imports per account across workers. Queued work
waits for capacity without consuming its failure retry budget. It permits
at most three redirects, globally routable DNS results only, and pins the
validated address with hostname TLS verification. Redirects repeat all checks.
No environment proxy or Pneumatic headers are used. The deadline is 60 seconds;
the streamed byte limit is min(25 MiB, configured storage limit), independent of
Content-Length. Pending unreferenced MCP files are eligible for cleanup after
24 hours only after rechecking attachment references.

## Verification and rollout

* Positive end-to-end flow: authorize, read kickoff, run, inspect task, upload/
  import, inspect upload status, attach, complete.
* Negative checks: incorrect PKCE/audience/scope, CSRF/redirect injection,
  revoked connection, disabled user, wrong tenant/file/field and billing gates.
* Reliability: ordinary repeated writes, response loss after commit,
  durable import restart, interrupted upload, two resource-server replicas.
* Files: Range/ticket expiry/revocation, DNS rebinding, unsafe redirects,
  unknown Content-Length, size/deadline bounds, partial-write cleanup.
* Regression: ordinary login/API keys, Zapier, workflow permissions and existing
  file service behavior. Run complete subsystem test suites before final review.
* Isolated staging first, then a limited production pilot. Actual Claude.ai/
  ChatGPT sign-in and tool calls must be recorded as acceptance evidence, not
  inferred from mocks, Inspector, OAuth consent or health endpoints.

There is no claim of production completion without deployment and live client
verification. Missing external credentials are reported explicitly; unaffected
implementation and verification continue without repeated approval questions.
