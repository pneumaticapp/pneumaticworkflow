# MCP rollout and recovery

The implementation uses the current Django backend and separate file service.
The additional MCP container is a resource server, not a second business backend.
Use `docs/mcp-design.md` for scope and `backend/docs/mcp-api.md` for API contracts.

## Configuration

Set the same `MCP_ENABLED`, `MCP_PUBLIC_URL` and `MCP_ISSUER_URL` across backend,
workers, frontend, storage and the MCP service. Use literal `yes` or `no`.
New MCP flags default to `no`. Only `yes` enables them; other values leave
them disabled without a configuration error.
Production examples are `https://my.pneumatic.app/mcp` and
`https://my.pneumatic.app`. The public resource URL must match exactly; moving
it invalidates existing audience-bound connections.

Generate two independent random secrets of at least 32 characters per environment:

| Setting | Recipients |
|---|---|
| `MCP_SERVICE_SECRET` | Backend and MCP resource server |
| `MCP_FILE_SERVICE_SECRET` | Backend, workers and file service |
| `MCP_BACKEND_URL` | MCP and storage; reachable private core HTTP address |
| `MCP_FILE_SERVICE_URL` | Backend, workers and MCP; private storage HTTP address |
| `MCP_REDIS_URL` | MCP replicas; same Redis database and authentication |
| `MCP_MAX_IMPORT_BYTES` | Backend, workers and storage; default 26214400 bytes, no larger than `FILE_MAX_FILE_SIZE` |
| `THROTTLE_14` | Backend; registration, default `10/min` (one request every 6 seconds) |
| `THROTTLE_15` | Backend; shared authorize/login scope, default `60/min` (one request per second) |
| `THROTTLE_16` | Backend; shared token/revoke scope, default `120/min` (one request every 0.5 seconds) |

Compose routes the private core through `http://pneumatic-nginx` because the
backend is served through a Unix socket. The private storage URL is
`http://file-service:8000`. The existing public file-service URL still serves
browser uploads and downloads. Do not interchange the public and private URLs.

Public OAuth uses the existing `CustomSimpleRateThrottle` through a small
adapter for the SDK's ordinary Django views. It runs before SDK hashing and
database writes and uses the backend's default cache (`CACHE_REDIS_URL` in
production), rate syntax and IP identification. All web replicas must share
that cache and the same rates. There is no separate OAuth Redis store.

Rates set a minimum interval between requests, not a burst allowance. Shared
scopes mean that authorize/login and token/revoke each use the same interval.
Exhaustion returns an OAuth JSON error with 429, `Retry-After` (seconds until
another request is allowed) and `Cache-Control: no-store`. A Redis error returns
503. Cache `get/set` follows the existing throttle's concurrency semantics;
it does not guarantee atomic admission for simultaneous requests.

IP identity follows the backend's DRF throttle settings, including `NUM_PROXIES`.
Ingress must normalize forwarded headers according to the deployed topology.
OAuth no longer has separate proxy CIDR or Unix-socket trust flags.

On Railway, create a separate service from `mcp/Dockerfile`, with private
networking and no extra public domain. Configure nginx `MCP_HOST` to its actual
private service hostname and port 8000. Set private backend and storage hosts
from the selected environment. Existing frontend routes and OAuth callbacks
remain on the public application host.

## Release order

1. Back up both databases and retain the currently deployed image references.
2. Apply Django and storage Alembic migrations using their existing release
   commands. OAuth, connection records and file tickets require migrations
   even while the feature is disabled. The new application migrations are
   Django `mcp.0001_initial` and storage `6ba2db086f1b` (after `5ba2db086f1a`).
   Apply the toolkit's migrations as part of the normal Django migration graph.
3. Deploy backend, worker/beat, storage and frontend changes with
   `MCP_ENABLED=no`, then update nginx routing. Verify ordinary login,
   workflows, API-key integration and file upload/download.
4. Deploy the MCP image. The service has no `/health` or `/ready` routes and
   no Docker healthcheck. After enabling it in staging, use an authenticated
   `tools/list` request on `/mcp` to verify transport, OAuth introspection and
   Redis together. With `MCP_ENABLED=no`, HTTP requests return 503.
5. In an isolated staging environment, configure secrets, URLs and shared Redis,
   then enable the feature across services. Check issuer/resource discovery,
   authorization, refresh/revocation, read/write operations, file lifecycle,
   concurrent retries and recovery after a worker restart.
6. Connect actual Claude.ai and ChatGPT test accounts to the public URL. Record
   successful sign-in and tool calls, including a write and file operation.
   Inspector or mocked tests do not establish compatibility with those clients.
7. Roll out to a limited production pilot only after that acceptance evidence.

The initial MCP migration chains were consolidated before release. If an
earlier MCP chain has already been applied to a disposable local test database,
recreate that database or roll back MCP with the earlier migration files before
switching to the consolidated files. An applied `0001_initial` or `6ba2db086f1b`
will not rerun automatically. Do not fake migration history on a database with
real data; keep its applied migration chain and plan a separate migration.

For local Compose, `start.sh` enables the `mcp` profile when the feature is on.
With direct Compose commands, explicitly select `--profile mcp`. Keep MCP's
port private; nginx provides the public `/mcp` endpoint. The proxy returns 503
when the optional MCP upstream is absent, without preventing nginx startup.

## Monitor and recover

Monitor authentication failures, throttling, dependency failures, tool latency,
pending import jobs and upload sessions that fail to become ready. Exclude
tokens, authorization codes, download tickets and source URL queries from logs
and telemetry. Notifications and webhooks use the ordinary Celery task/provider
behavior; a successful tool response does not prove downstream delivery.

After an ambiguous write timeout, inspect current state before retrying.
Repeated workflow runs or comments create new objects. A revoked connection
must fail for upload capabilities and download tickets too.

For an immediate feature rollback, set `MCP_ENABLED=no` across all services.
Keep schema additions and durable state so recovery can reconcile previously
committed work. Do not reverse migrations as an emergency rollback. Restore
the prior application images only after checking schema compatibility. Secret
rotation requires coordinated recipient updates and client reconnection where
the associated connection is revoked.

Deployment, CI and real-client acceptance are separate evidence. Record exact
image revisions, migration results and test outcomes in the release report.

## Local verification

The subsystem suites cover OAuth and permissions in Django, the MCP transport
and schemas, frontend consent/upload flows, and storage lifecycle/security.
`scripts/tests/test_mcp_nginx.py` runs both nginx configurations against isolated
Docker upstreams, including absent-service behavior and log redaction.
`mcp/tests/docker-smoke.ps1 -Build` checks the built MCP image with real Redis and
both supported protocol generations, including authenticated startup on the
configured port (8123 in the custom-port case). Its core upstream is a contract
double. Startup checks use `tools/list`; they do not need diagnostic routes.

`scripts/tests/test_mcp_core_http.py` instead calls genuine Django business and
OAuth views over HTTP. Run it with backend test dependencies, the dependencies
from `mcp/pyproject.toml`, an isolated PostgreSQL database and
`MCP_TEST_REDIS_URL`; use `PYTHONPATH=backend:mcp/src` and the backend pytest
configuration. On Windows, use the platform path separator for `PYTHONPATH`.

For the additional file cycle, set `MCP_STORAGE_SMOKE_URL` to the private test
storage URL and bind pytest's live server to `localhost:18081`. Start
`python -m tests.live_mcp_server --port 18083` with storage dependencies,
`PYTHONPATH=storage`, `POSTGRES_DB=mcp_contract_files`, explicit isolated database
credentials and the synthetic secrets defined in the HTTP test. Both processes
must share a loopback network; Docker can use the core test container's network
namespace. The helper applies actual storage Alembic migrations and replaces
only S3 bytes with memory. This verifies upload acknowledgement, attachment,
metadata, tickets, Range and revocation without touching an external provider.
Never use a production database or real account for these helpers.
