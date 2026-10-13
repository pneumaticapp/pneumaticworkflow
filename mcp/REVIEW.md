# MCP protocol review, 2026-10-09

## Execution layer removal — 2026-10-13

McpExecutionMiddleware, the generic MCP idempotency ledger and notification
outbox have been removed. Core writes use the ordinary backend behavior and
Celery tasks. Write tool schemas no longer require idempotency_key, and their
idempotentHint is false. OAuth authentication, live permissions, upload sessions
and durable URL import jobs remain. The single initial migration mcp.0001_initial creates only the current MCP
models; execution tables and the obsolete outbox schedule are not created.

Final local checks: 555 backend/MCP write regressions passed; 338 MCP resource
server tests passed; the real core/OAuth/SDK HTTP lifecycle passed. Django system
checks, migration drift checks, Ruff and whitespace checks passed. An isolated
migration readback verified removal of both execution tables, obsolete beat
schedule and refresh of the beat change timestamp, with uploads/imports retained.
No production migration, commit, push or deployment was performed.

The dated results and implementation descriptions below are historical
snapshots; their replay and notification-outbox claims no longer describe the
current implementation.

The subsequent module/catalogue/execution refactoring on 2026-10-12 and its
verification are documented in
[MCP standards review](../docs/mcp-review.md#logical-refactoring-2026-10-12).
That revision exposes 18 tools; the older counts below describe prior runs.

Scope: `mcp/**`, working tree based on
`3d6a407d93ae1be5d2d12960fa5ccbba0499c336`.
Both `D:/Dev/knowledge/.agent/workflows/backend-revue.md` and
`backend-tests.md` were read in full. No commit, push or deployment.
Root scripts, backend, storage, frontend, nginx and CI remain parent-owned.

## Confirmed defects and fixes

| Defect | Fix | Regression evidence |
| --- | --- | --- |
| Settings accepted `/prefix/mcp`, although the HTTP transport and core require exactly `/mcp`. An issuer from another origin or an issuer with a path was also accepted. | Require the exact resource path and the same literal scheme/authority as core; require an origin-only issuer. Build the protected-resource metadata route with the SDK's canonical URL helper. | `test_settings__wrong_public_path__validation_error`, `test_settings__inconsistent_issuer__validation_error`, metadata HTTP cases. |
| The source-token regex bounded its token alphabet, but allowed an unlimited trailing `=` suffix. | Bound the complete token to 4096 characters before introspection. | `test_verify_token__overlong_credentials__before_introspection` covers both token alphabet and padding, with no upstream request. |
| URL parsing silently stripped control characters and did not validate ports. | Reject control/space characters and invalid or zero ports during configuration validation. | `test_settings__unsafe_public_url__validation_error`. |
| An enabled service accepted an all-space service secret of sufficient length. Validation failures could also echo configuration input. | Reject blank secrets and hide input in Pydantic validation text. | Invalid enabled-secret cases and assertions that sensitive URL input is absent from exception text. |
| Several tests combined independent HTTP outcomes and performed asynchronous calls after their assertion block. | Separate initialization, metadata, health, route rejection, SDK discovery/call, file-scope denial/success, disabled endpoints and body-limit/timeout cases. Ensure overload teardown releases and awaits the pending call even on failure. | Final HTTP/protocol regression run and AST review. |

Formatting mistakes introduced while wrapping strings were corrected before
final validation. The final AST audit found no literal calls, untyped function
arguments, `-> None`, or awaits/comprehensions inside assertions.

## Structural changes

- The seven-line `scopes.py` module was removed. `settings.py` is now the
  canonical location for the supported permission vocabulary used by metadata,
  introspection, delegation and tool declarations. The redundant auth re-export
  list was removed.
- Introspection retains separate unavailable-service and invalid-token
  outcomes. Once required response fields are validated, it reads those fields
  directly and splits scopes once; duplicate active/expiry/scope type checks
  were removed.
- `files.py` already contained substantive canonical identity/path validation,
  rather than pass-through wrappers. It remains a separate file boundary.
  Unicode, spaces, normalization differences and legacy file spelling remain
  intact; ambiguous paths remain rejected before storage HTTP.
- Internal calls use named parameters; function arguments are annotated and
  void-return annotations were removed. Ruff's persistent line length is 79.
- Test infrastructure and Redis process fixtures are in `conftest.py`; test
  modules contain test functions rather than global helpers or test classes.
  The result wrapper and a one-use scope-call wrapper were removed. Tests use
  explicit AAA blocks, scenario names and direct ordinal assertions.
- `outputs.py` binds the list collector explicitly instead of using a mutable
  closure/default tied to the result-size loop. Output schemas and the 64 KiB
  result contract are preserved.

## Dependency graph and review order

```text
create_app / real SDK transport
|-- McpEnabledMiddleware -> feature-off 503
|-- OAuthResponseMiddleware -> challenges / tool HTTP status / auth outage
|-- SecurityHeadersMiddleware -> no-store / no-referrer
|-- SDK TransportSecuritySettings -> host/origin checks
|-- Starlette routes -> exact /mcp path, POST only
|-- Uvicorn -> process concurrency limit
|-- CoreTokenVerifier.verify_token
|   `-- CoreClient.introspect -> private -> _request -> _json_body
|-- ToolHandlers.list_tools
|   |-- _charge -> RedisRateLimiter.acquire
|   `-- ToolSpec.schema -> input/output models + OAuth schemes
|-- ToolHandlers.call_tool
|   |-- Pydantic validators + recursive file-scope inference
|   |-- _charge -> RedisRateLimiter.acquire
|   |-- CoreClient.call -> private delegation -> _request
|   |   |-- Settings.backend_endpoint
|   |   `-- Settings.file_endpoint -> validate_file_path -> file_id_segment
|   |-- normalize -> Compact field/task/workflow/event converters
|   `-- public_error / auth_challenge -> HTTP + tool-result metadata
`-- lifespan -> CoreClient.close + RedisRateLimiter.close
```

Functions were reviewed from the leaves: configuration validators and URL
builders; file identity/path validation; result redaction and JSON bounds;
error/challenge formatting; Redis acquire; Compact converters and
normalization; private HTTP/introspection/delegation; token verification;
input validators and scope inference; tool schema/middleware/callbacks;
focused HTTP middleware, lifespan and process startup.

## Test cases

| Tested function / boundary | Scenario | Annotation | Test |
| --- | --- | --- | --- |
| Settings validators | Default HTTPS and explicit HTTP loopback origins, IPv6, custom port | Preserve defaults and configured listening port | Yes |
| Settings validators | Prefix/trailing/incorrect public path; foreign/path/port issuer | Match the current core configuration contract | Yes |
| Settings validators | Malformed port, control characters, credentials, query, fragment, blank enabled secret | Reject at startup without echoing inputs | Yes |
| file_id_segment / file_endpoint | Legacy Unicode/space IDs and both storage paths | Preserve the exact storage identity | Yes |
| file_id_segment / file_endpoint | Null/type errors, length limits, traversal, control/bidi characters and noncanonical encoding | Fail before storage HTTP; assert exception text | Yes |
| Token verifier | Inactive, expired, malformed/private outage, bad audience/scope/identity and excessive token length | Distinguish 401 from dependency 503 | Yes |
| HTTP transport / middleware | Wrong Host/Origin, unsupported routes, overload, disabled service, body size limit | SDK checks security, router restricts methods, Uvicorn limits concurrency; rejected calls do not execute tools | Yes |
| Metadata / list_tools | Both protected-resource metadata paths and all 16 tool OAuth schemes on both protocol versions | Preserve discovery for read/write/file-only consent | Yes |
| Official SDK | Legacy initialization, modern discovery, header/body mismatch and SDK legacy/auto clients over TCP | Retain official SDK protocol processing | Yes |
| Tool schemas / delegation | Every fixed route, invalid arguments, target XOR, concurrent principals and malformed grants | Exact body/path/scopes; no source bearer in business calls | Yes |
| File scope inference | Nested uploads, existing file links, ordinary/external text, denied clears and consented clears | Core remains authoritative for actual field types | Yes |
| Core errors | Source revocation, private service auth failure, object denial, structured scope denial, network uncertainty | Safe messages/challenges, no automatic write retries | Yes |
| Attachment orchestration | Exact encoded grants, authorized metadata/ticket, unsafe file identity | No cross-boundary credential forwarding | Yes |
| normalize / schemas | REST selections, kickoff fieldsets and large serializer results | Keep compact schemas and result bound | Yes |
| Redis limiter | Two processes sharing connection/account budgets; independent principals; dependency outage | Real Redis; no mocked limiter/ORM/transaction | Yes |
| Docker | Production image, legacy + modern wire behavior and tool discovery on port 8123 | Nonroot, read-only service containers | Yes |

The external core/storage HTTP interfaces use `httpx.MockTransport` boundary
doubles whose recorded requests are asserted directly. The MCP SDK, TCP server
and Redis remain real. There is no ORM, manager or transaction mock in this
scope, and no real notification/provider task is run by these doubles. The
parent owns real Django ORM/outbox and storage integration verification.

## Required protocol exceptions

- This isolated resource server uses Pydantic SDK schemas, not Django/DRF
  business serializers. DRF validation envelopes and translation MSG identifiers
  remain the core business API's responsibility.
- Standard SDK callbacks, ASGI callback invocation and Redis Lua's variadic
  argument protocol can require positional parameters. They are retained as
  external interface conventions; internal business calls use named arguments.
- OAuth `WWW-Authenticate`, 401/403/503 distinctions and protected-resource
  metadata remain protocol responses. Tool errors preserve `isError`, safe
  structured content and ChatGPT's `_meta["mcp/www_authenticate"]` challenge.
- `securitySchemes` and `_meta.securitySchemes` survive both SDK wire versions
  through the existing declared model/middleware extension. The SDK is not
  patched and the 16-tool contract is unchanged.

References: [MCP authorization](https://modelcontextprotocol.io/specification/2025-11-25/basic/authorization),
[OpenAI SDK reference](https://developers.openai.com/plugins/reference).

## Validation

Commands run from `mcp` with project-local `UV_CACHE_DIR` and the locked
Python 3.12 runtime:

```powershell
$env:UV_CACHE_DIR = Join-Path $PWD '.uv-cache'
$env:UV_LINK_MODE = 'copy'
uv sync --locked --offline --python '.python/cpython-3.12-windows-x86_64-none/python.exe'
uv run --locked --offline ruff check .
uv run --locked --offline ruff format --check .
$env:MCP_TEST_REDIS_URL = 'redis://127.0.0.1:53634/15'
uv run --locked --offline pytest -q --basetemp=.pytest_cache/review-basetemp
```

Locked dependency installation, lint and formatting passed. Full suite with
real Redis: **323 passed in 82.54 seconds, no skips**. After splitting the two
remaining SDK/discovery scenarios, only the changed HTTP/protocol tests were
rerun; their final result is recorded below.

```powershell
uv run --locked --offline pytest -q tests/test_protocol.py tests/test_http.py --basetemp=.pytest_cache/review-protocol
```

Final changed-test rerun: **239 passed in 54.17 seconds**, exit 0.
Final locked Ruff lint and format checks passed (21 Python files).
The final AST review passed argument typing, void-return annotation rules,
literal-call detection, scenario names, AAA blocks and assertion boundaries.
The result now contains 325 collected cases: the two additional cases split
SDK discovery and calls; the unchanged configuration/file/Redis cases retain
their successful full-run coverage. No confirmed defect remains in the
reviewed protocol source or its tests.

From the repository root:

```powershell
docker build --tag pneumatic-mcp-review:20261009 mcp
& .\mcp\tests\docker-smoke.ps1 -Image 'pneumatic-mcp-review:20261009'
```

Both commands exited 0. The image installs production dependencies with
`uv sync --locked --no-dev --no-editable`. Docker smoke passed for
`2025-11-25` and `2026-07-28`: discovery, 16 tools, delegation, Unicode file
tickets, structured scope upgrades/clears, safe 401/403/503 errors and no write
retry. That earlier run also tested a Docker healthcheck on port 8123;
the middleware cleanup below removes it and checks actual MCP requests instead.

No shared Docker resource was deleted. Smoke containers/networks clean up their
own unique names; the separate review Redis is removed after verification.
These checks establish local protocol behavior, not deployment or acceptance
by a live Claude.ai/ChatGPT account.

## Changed paths

- `mcp/pyproject.toml`
- `mcp/src/pneumatic_mcp/{__main__,app,auth,client,errors,files,limiter,outputs,security,settings,tools}.py`
- Removed: `mcp/src/pneumatic_mcp/scopes.py`
- `mcp/tests/{conftest,redis_worker,smoke_core,smoke_probe,test_files,test_http,test_protocol,test_redis}.py`
- Added: `mcp/tests/test_settings.py`, `mcp/REVIEW.md`

`uv.lock`, `Dockerfile`, and `tests/docker-smoke.ps1` were unchanged in that
earlier review. The cleanup below subsequently changes the latter two files.

## Middleware cleanup — 2026-10-12

Removed `RequestGate`, `/health`, `/ready`, their Docker/Compose healthchecks
and the unused Redis readiness method. `app.py` now assembles the SDK server,
routes and lifespan. One `middleware.py` holds focused feature-enable,
OAuth-response and security-header classes, registered through Starlette's
middleware stack as in the file service. The wrappers use ASGI directly so
they preserve streaming response bodies.

Host/Origin validation remains in the SDK; exact paths and POST-only `/mcp`
use Starlette routes; process overload uses Uvicorn. Shared connection/account
budgets remain in Redis. OAuth scope challenges, tool-result metadata, 401/403,
dependency 503 and rate-limit 429 behavior are preserved. Privacy headers now
also cover the disabled response, without duplicate header values.

The second review caught a configuration edge: Uvicorn counts the accepted
connection before enforcing its limit, so a value of 1 rejects every request.
The allowed minimum is now 2; the default remains 32. Real HTTP tests prove
that the minimum accepts a first request and rejects overload before token
introspection. Startup checks now call authenticated `tools/list`, exercising
the transport, token verifier and Redis together, including port 8123.

Final verification:

- Entire MCP suite: **338 passed in 71.46 seconds, no skips**, including two
  real processes sharing an isolated Redis 6.2 instance.
- Ruff lint and formatting: passed for all 22 Python files.
- Final production image build and Docker HTTP smoke: passed for both protocol
  generations, OAuth/delegation/files and authenticated startup on port 8123.
- Image configuration contains no healthcheck; both Compose configurations
  parse successfully; `git diff --check` passes.
- The actual core HTTP helper now checks resource metadata instead of `/ready`.
  It passes lint; the earlier complete Django/storage HTTP cycle was not rerun
  for this transport-only cleanup.

The final review found no remaining confirmed defect in this scope. Results
are local; no commit, push, deployment or live-client acceptance was performed.
