# Pneumatic MCP server

## About

Connects compatible MCP clients to a Pneumatic installation using Streamable HTTP or stdio. Tools read and update tasks, workflows, templates, files, reports, users, groups and datasets through the Pneumatic API, with the permissions of the API key owner.

### What you can do

| Area                      | Capabilities                                                                                                                                                   | Example tools                                                                          |
| ------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| Tasks                     | Find assigned work, inspect fields and history, complete or return tasks, comment, change due dates and performers, and update checklists.                     | `list_tasks`, `get_task`, `complete_task`, `comment_on_task`                           |
| Workflows                 | Start workflows from templates, inspect progress and history, update kickoff values, snooze/resume, return to an earlier step, finish or terminate a workflow. | `run_workflow`, `get_workflow`, `update_workflow`, `snooze_workflow`                   |
| Templates                 | Browse templates, create and edit process steps and forms, clone templates, and use the template library.                                                      | `get_template`, `create_template`, `add_template_step`, `create_template_from_library` |
| Files                     | List attachments, upload text or binary content, download files, and request a browser upload link with status tracking.                                       | `list_attachments`, `upload_file`, `download_file`, `create_upload_link`               |
| Reports                   | Read dashboard metrics and highlights, count workflows, inspect field values and step statistics.                                                              | `get_dashboard`, `list_highlights`, `count_workflows`, `get_template_step_stats`       |
| People and reference data | Look up users, groups and datasets; manage them with the required permissions; set absences, reassign work and read notifications.                             | `list_users`, `create_group`, `list_datasets`, `set_vacation`                          |

The client discovers the enabled tools, their descriptions and argument schemas through MCP `tools/list`. It calls a tool through `tools/call`; the tools do not each have a separate REST endpoint.

The server uses the API key owner's permissions. Some operations require an admin or account owner. `READ_ONLY=true` hides write tools, and `TOOLSETS` restricts the offered areas. Browser upload links require HTTP mode and configured file storage. List results are paginated, and large results can be shortened (`truncated=true`); clients must check these fields before treating a result as complete. Writes can notify people or trigger integrations, and an uncertain write result must be checked before retrying.

| Transport | Client connection                     | Authentication                                                                                                                  |
| --------- | ------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| HTTP      | Streamable HTTP at `<PUBLIC_URL>/mcp` | OAuth with PKCE: each user enters their API key on the consent page. A raw API key in `Authorization: Bearer <key>` also works. |
| stdio     | Client starts a local Node.js process | `PNEUMATIC_API_KEY` in the process environment.                                                                                 |

Create a key in your installation under **Integrations → Your API Keys → Create** (account owner or admin). The full key is shown once. To revoke access, delete the key there; HTTP key validation is cached for up to five minutes.

## Configuration

Use the **repository-root `.env`** for [docker-compose.yml](../docker-compose.yml), [docker-compose.src.yml](../docker-compose.src.yml) and `start.sh`. The **Root Compose setting** column shows which installation variable supplies each process variable. Compose does not read `mcp/.env`; settings marked **Compose** are fixed in the bundled service, and **—** means the setting is not passed by the bundled service. To change a fixed setting or pass an additional variable, add it to the service's `environment` in a Compose override; adding it only to the root `.env` is insufficient.

For a standalone process, create `.env` in `mcp/` from the example in [Standalone Docker](#standalone-docker) or [For Developers](#for-developers) and use the **Process variable** names below for other settings. Load it explicitly with `node --env-file=.env`; `npm start` and `npm run dev` do not load env files. Exported shell variables take precedence over the env file. Defaults below apply when a variable is omitted.

| Process variable                      | Root Compose setting                       | Default                                                                                                                                                     | Meaning / example                                                                                                                                                                                                                                                                                                                           |
| ------------------------------------- | ------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `BACKEND_PRIVATE_URL`                 | `BACKEND_PRIVATE_URL`                      | Process: `https://api.pneumatic.app`; Compose: `http://pneumatic-nginx`                                                                                     | Backend HTTP(S) base URL reachable from the connector. For a host process, e.g. `http://localhost:8001`; remotely, e.g. `https://api.example.com`. Do not append an API resource path.                                                                                                                                                      |
| `PNEUMATIC_FILES_URL`                 | Derived from `FILE_PORT`                   | Process: `FILE_SERVICE_URL`, otherwise Cloud storage for the default API or unset for a custom API; Compose: `http://pneumatic-file-service:<FILE_PORT>`    | Address used for storage requests. A standalone process can use its public file URL here. If storage requests use an internal address, set the public address separately in `FILE_SERVICE_URL`.                                                                                                                                             |
| `FILE_SERVICE_URL`                    | `FILE_SERVICE_URL`                         | Process: `PNEUMATIC_FILES_URL`, otherwise `https://my.pneumatic.app/files` for the default API or unset for a custom API; Compose: `http://localhost/files` | Public file URL prefix matching the backend, used in links and download URL validation, e.g. `https://app.example.com/files`.                                                                                                                                                                                                               |
| `FRONTEND_URL`                        | `FRONTEND_URL`                             | Process: public storage URL with a final `/files` removed, otherwise unset; Compose: `http://localhost`                                                     | Web app URL for task, workflow and template links. Set explicitly if storage uses another path; unset means no web app links in results.                                                                                                                                                                                                    |
| `MCP_TRANSPORT`                       | Compose: `http`                            | `stdio`                                                                                                                                                     | `stdio` or `http`. Command-line `--http` / `--stdio` overrides this value.                                                                                                                                                                                                                                                                  |
| `PNEUMATIC_API_KEY`                   | —                                          | Unset                                                                                                                                                       | Required for stdio and smoke scripts. HTTP requests supply a key per user; leave this unset on a shared HTTP server.                                                                                                                                                                                                                        |
| `TOOLSETS`                            | `MCP_TOOLSETS`                             | All groups                                                                                                                                                  | Comma-separated groups listed below, or `all`; empty also selects all. Unknown names fail startup.                                                                                                                                                                                                                                          |
| `READ_ONLY`                           | `MCP_READ_ONLY`                            | `false`                                                                                                                                                     | `true`/`yes`/`1` hides write tools; `false`/`no`/`0` or empty permits writes.                                                                                                                                                                                                                                                               |
| `LOG_LEVEL`                           | `MCP_LOG_LEVEL`                            | `info`                                                                                                                                                      | `debug`, `info`, `warn`, `error`, `off`; logs are JSON lines on stderr. Invalid values fail startup.                                                                                                                                                                                                                                        |
| `HOST`                                | Compose: `0.0.0.0`                         | `127.0.0.1`                                                                                                                                                 | HTTP listen address. A standalone container needs `0.0.0.0` to accept connections from its proxy. Ignored in stdio mode.                                                                                                                                                                                                                    |
| `PORT`                                | —                                          | `3000`                                                                                                                                                      | HTTP listen port, integer from `1` to `65535`. Ignored in stdio mode.                                                                                                                                                                                                                                                                       |
| `PUBLIC_URL`                          | `MCP_PUBLIC_URL`, otherwise `FRONTEND_URL` | Process: `http://localhost:<PORT>`; Compose: `http://localhost` if both root settings are unset                                                             | Connector origin for OAuth metadata, consent and upload links, e.g. `https://mcp.example.com`. No path, query, fragment or credentials; HTTPS required except for `localhost`, `127.0.0.1`, `[::1]`. Do not append `/mcp`. A separate origin needs its own DNS, TLS and proxy routing. Ignored in stdio mode.                               |
| `TOKEN_SECRET`                        | `MCP_SECRET`                               | Unset                                                                                                                                                       | Required for HTTP; at least 32 characters. Generate once with `openssl rand -hex 32`. `start.sh` generates a separate 64-character hex secret if missing and the connector is enabled; direct Compose startup requires an explicit value. Keep across restarts; rotation invalidates OAuth tokens and registrations. Ignored in stdio mode. |
| `OAUTH_REPLAY_FILE`                   | Compose: `/state/replay.json`              | Unset                                                                                                                                                       | Required for HTTP: existing, writable persistent file containing spent OAuth identifiers and revocations. Local example: `./.state/replay.json`. Compose mounts the host directory `mcp/.state` at `/state`; preserve it on upgrades. Ignored in stdio mode.                                                                                |
| `OAUTH_REPLAY_CREATE_ON_EMPTY_VOLUME` | Compose: `true`                            | Unset: creation disabled                                                                                                                                    | Docker entrypoint setting, not read by Node.js. Exactly `true` creates the replay file only if its directory exists and is empty, initializing a fresh volume without silently replacing lost state.                                                                                                                                        |
| `OAUTH_ALLOWED_REDIRECT_HOSTS`        | `MCP_OAUTH_ALLOWED_REDIRECT_HOSTS`         | `claude.ai,claude.com,www.cursor.com,localhost,127.0.0.1,[::1]`                                                                                             | Comma-separated OAuth callback hostnames without schemes, paths or ports. Set the full list when adding a client; `*` permits any host. Ignored in stdio mode.                                                                                                                                                                              |
| `RATE_LIMIT_PER_MINUTE`               | `MCP_RATE_LIMIT_PER_MINUTE`                | `120`                                                                                                                                                       | Non-negative integer, MCP requests per API key per minute; `0` disables this limit. Consent failures have a separate fixed limit of 10 per client IP per minute. Ignored in stdio mode.                                                                                                                                                     |
| `TRUST_PROXY`                         | —                                          | `loopback,uniquelocal`                                                                                                                                      | Trusted reverse proxy addresses/subnets, hop count, or `true`/`false`. Controls trusted `X-Forwarded-For` values for client IP limits; match your proxy network. Ignored in stdio mode.                                                                                                                                                     |
| `METRICS_TOKEN`                       | —                                          | Unset: `/metrics` disabled                                                                                                                                  | At least 16 characters; enables Prometheus metrics with `Authorization: Bearer <METRICS_TOKEN>`. Ignored in stdio mode.                                                                                                                                                                                                                     |
| —                                     | `MCP_ENABLE`                               | Unset: not decided                                                                                                                                          | Root setting only. `yes` or `no`, the answer to the `start.sh` question about the connector; while empty, `start.sh` asks it and derives `COMPOSE_PROFILES` from the answer. Empty it to answer again: a hand-edited value does not change `COMPOSE_PROFILES`.                                                                              |
| —                                     | `COMPOSE_PROFILES`                         | Unset                                                                                                                                                       | Root setting only. Rewritten by `start.sh` whenever one of its dialogs runs; for direct Compose startup include `mcp` yourself, or pass `--profile mcp`. Combine profiles on one comma-separated line, e.g. `logs-otlp,mcp`.                                                                                                                |
| —                                     | `FILE_PORT`                                | `8000`                                                                                                                                                      | Root setting only. File-service container port used to construct the storage request address.                                                                                                                                                                                                                                               |

Backend, file and app URLs accept HTTP(S) without credentials, query strings or fragments; trailing slashes are removed. `localhost` inside a container refers to that container, not the host. `PUBLIC_URL` and `FRONTEND_URL` may differ: for example, the connector can use `https://mcp.example.com` while the web app uses `https://app.example.com`.

| `TOOLSETS` group | Contents                                                                                                |
| ---------------- | ------------------------------------------------------------------------------------------------------- |
| `core`           | Tasks, workflows, template lookup/launch, comments, notifications, vacation, user/group/dataset lookup. |
| `files`          | Attachments, uploads and downloads; browser upload links require HTTP mode.                             |
| `design`         | Template creation, editing and the template library.                                                    |
| `analytics`      | Dashboard, highlights, workflow counts, step statistics and field-value reports.                        |
| `admin`          | User, group and dataset management; reassignment.                                                       |

## Installation / Get started

### With the Pneumatic stack

Requires a configured Pneumatic installation and Docker Compose. Run commands from the repository root. For remote clients, configure HTTPS for the installation (`SSL=yes` with the bundled nginx) and set `FRONTEND_URL` and `FILE_SERVICE_URL` to your public addresses. HTTP is accepted only on loopback.

1. Run `./start.sh`. While `MCP_ENABLE` is empty, the script asks whether to enable the connector, writes `MCP_ENABLE` and `COMPOSE_PROFILES` to the root `.env` and generates `MCP_SECRET` if missing, including on existing installations. It then asks which version to start; select **From sources** to build this checkout. To change the answer later, empty `MCP_ENABLE` and run `./start.sh` again.
2. Alternatively, start directly with Compose: generate a secret with `openssl rand -hex 32`, set `MCP_SECRET=<generated value>` in the root `.env` (paste the value, not the command), then run:

   ```bash
   docker compose --profile mcp up -d --build
   ```

3. Check the connector:

   ```bash
   docker compose --profile mcp ps mcp
   docker compose --profile mcp logs --tail=50 mcp
   docker compose --profile mcp exec mcp node -e "fetch('http://127.0.0.1:3000/healthz').then(r => r.text()).then(console.log)"
   curl -i -X POST https://mcp.example.com/mcp -H 'Content-Type: application/json' --data '{}'
   curl -fsS https://mcp.example.com/.well-known/oauth-authorization-server
   ```

   Replace `https://mcp.example.com` with `MCP_PUBLIC_URL` if set, otherwise `FRONTEND_URL`. Health returns `{"status":"ok"}`; unauthenticated `/mcp` returns **401** with `WWW-Authenticate`; OAuth metadata contains your public origin. These checks do not verify backend access: connect a client and call `get_current_user` next.

The bundled nginx has one proxy location, `/mcp/`. It internally normalizes `/mcp` to `/mcp/` and forwards the public `/.well-known/oauth-*` discovery namespace through that same entry without redirecting the client. Express handles OAuth, uploads, metadata and MCP requests inside one `/mcp` router; nginx does not enumerate the application endpoints. The standard public discovery URLs remain `/.well-known/oauth-protected-resource/mcp` and `/.well-known/oauth-authorization-server`. A standalone process also accepts these root discovery URLs and normalizes them into the same router. `/healthz` and `/metrics` remain internal container routes. With the connector stopped, its nginx routes return 502.

To disable it, empty `MCP_ENABLE`, run `./start.sh` and answer no; the script rewrites `COMPOSE_PROFILES` without `mcp`. Setting `MCP_ENABLE=no` by hand leaves `COMPOSE_PROFILES` as is; with direct Compose commands, remove `mcp` from the enabled profiles yourself. Neither stops an already running container: remove it with `docker compose --profile mcp rm -sf mcp`.

When upgrading an earlier connector configuration, replace `MCP_ENABLED=true` with `MCP_ENABLE=yes`. If you set `MCP_TOKEN_SECRET`, copy its value to `MCP_SECRET` before startup to preserve existing sessions; otherwise a new independent secret is generated. Standalone installations use `BACKEND_PRIVATE_URL` for the backend address and rename `PNEUMATIC_APP_URL` to `FRONTEND_URL`; the old `PNEUMATIC_FILES_INTERNAL_URL` is replaced by `PNEUMATIC_FILES_URL` for requests and `FILE_SERVICE_URL` for the public URL.

### Standalone Docker

Run from `mcp/`. Create `.env` with your installation's addresses and HTTP secret; other settings are described in [Configuration](#configuration). The API and storage request addresses must be reachable from the container.

```dotenv
BACKEND_PRIVATE_URL=https://pneumatic.example.com
FRONTEND_URL=https://pneumatic.example.com
PNEUMATIC_FILES_URL=https://pneumatic.example.com/files
PUBLIC_URL=https://mcp.example.com
TOKEN_SECRET=<output of openssl rand -hex 32>
MCP_TRANSPORT=http
HOST=0.0.0.0
OAUTH_REPLAY_FILE=/state/replay.json
OAUTH_REPLAY_CREATE_ON_EMPTY_VOLUME=true
```

The image has no entrypoint of its own, so pass the one that creates the replay file on a fresh volume together with the start command:

```bash
docker build -t pneumatic-mcp:local .
docker volume create pneumatic-mcp-state
docker run -d --name pneumatic-mcp --restart unless-stopped \
  --env-file .env \
  -v pneumatic-mcp-state:/state \
  -p 127.0.0.1:3000:3000 \
  --entrypoint /app/mcp-entrypoint.sh \
  pneumatic-mcp:local node dist/index.js
```

Put a TLS reverse proxy in front of `127.0.0.1:3000`. Forward `/mcp` and its subpaths. Forward public OAuth discovery requests either unchanged or internally rewritten from `/.well-known/oauth-*` to `/mcp/.well-known/oauth-*`, as in the bundled [MCP proxy location](../nginx/includes/location_mcp.conf). Preserve `Host`, set trusted forwarding headers, disable response buffering and allow request bodies of at least 26 MiB. Keep upload-token paths out of access logs. `PUBLIC_URL` must match the externally reachable origin.

### Connect a client

For any client supporting **Streamable HTTP**, configure:

| Setting                    | Value                                                                                                                                  |
| -------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| Server URL                 | `<PUBLIC_URL>/mcp`, e.g. `https://mcp.example.com/mcp`.                                                                                |
| Authentication             | OAuth authorization code with PKCE S256 and dynamic client registration. Each user enters their own API key on the consent page.       |
| Alternative authentication | `Authorization: Bearer <Pneumatic API key>` for clients supporting custom headers. Keep the key in the client's private configuration. |

For clients using the `mcpServers` JSON format, the remote configuration is:

```json
{
  "mcpServers": {
    "pneumatic": {
      "url": "https://mcp.example.com/mcp"
    }
  }
}
```

Configuration file names and fields depend on the client. OAuth discovery is at `/.well-known/oauth-protected-resource/mcp` and `/.well-known/oauth-authorization-server`; no pre-registered client secret is required. Add the client's callback hostname to `OAUTH_ALLOWED_REDIRECT_HOSTS` if absent. Desktop clients can use loopback HTTP callbacks. For local processes, use the [stdio configuration](#local-stdio-client) below.

Examples for specific clients:

| Client                                                        | Setup                                                                                                                                                                                                                                                                                 |
| ------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [Cursor](https://cursor.com/docs/mcp)                         | Put the JSON above in `.cursor/mcp.json` for a project or `~/.cursor/mcp.json` for your user, then authenticate. The documented web callback is `https://www.cursor.com/agents/mcp/oauth/callback`; desktop uses `http://localhost:8787/callback`. Both hosts are allowed by default. |
| [Claude](https://claude.com/docs/connectors/building/testing) | **Settings → Connectors → Add custom connector**; supply the server URL and complete consent.                                                                                                                                                                                         |
| [Claude Code](https://code.claude.com/docs/en/mcp)            | Run `claude mcp add --transport http pneumatic https://mcp.example.com/mcp`, then authenticate through `/mcp`.                                                                                                                                                                        |

Try “Show my overdue tasks” or “Start the onboarding workflow.” Writes use the key owner's permissions; `READ_ONLY=true` hides write tools. Destructive tools are annotated and request confirmation when the client supports forms; other clients are instructed to confirm before calling them. Compatibility must be verified in each client version you intend to support.

### Data handling and privacy

- The server processes API keys, tool arguments, results and files to execute requests. It sends account credentials only to the configured API and storage; downloads from public HTTPS URLs do not carry those credentials. Results are returned to the connected client, whose provider processes them under its own terms.
- OAuth tokens contain the encrypted API key: authorization codes last five minutes, access tokens one hour, refresh tokens 90 days and rotate on use. The replay ledger stores identifiers and expirations, not keys; expired entries are removed during compaction. User/group directories and successful key checks are cached in memory for five minutes, rejected keys for one minute. Rate limits also use in-memory key hashes and client IPs.
- Files persist in Pneumatic storage. Upload links expire after one hour; their in-memory status records become eligible for cleanup 24 hours after expiry and are lost on restart. Application logs contain request metadata, status and timing, not credentials or tool contents. Hosting operators control log retention and proxy logging.
- Disconnect in the client and delete the API key in Pneumatic to revoke access; the key-check cache can delay rejection by five minutes. For the maintained hosted service, the publisher's privacy policy and support contact are recorded in [listing.json](distribution/listing.json). For another deployment, contact its operator for its privacy policy, retention settings and deletion requests.

### State and restarts

Run **one HTTP process**. The replay ledger is file-based; upload links, caches and rate limits are in memory. Multiple replicas require shared stores.

- Compose mounts the host directory `mcp/.state` at `/state`; it holds `replay.json`: spent authorization codes, refresh-token identifiers and session revocations with expiry times. It contains no API keys or uploaded files. The directory persists across container replacement, host restarts and `docker compose down -v`; it is excluded from git and the image build context.
- Keep the directory and `TOKEN_SECRET` on upgrades. Docker creates the directory as root on first start, and the container writes the ledger as root with mode `0600`, so back up or move it with root privileges. If the ledger is lost or restored from an older copy, rotate the secret before creating a new ledger; users must reconnect. Reusing the old secret with missing records allows spent tokens to be accepted again.

### Troubleshooting

| Symptom                               | Check                                                                                                                           |
| ------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| Startup reports `Configuration error` | The named variable in the log, secret length, replay file existence and write permissions.                                      |
| 403 through the proxy                 | Original `Host` is preserved and matches `PUBLIC_URL`; the origin is allowed.                                                   |
| OAuth fails before consent            | All OAuth paths are forwarded and the callback hostname is in `OAUTH_ALLOWED_REDIRECT_HOSTS`.                                   |
| Consent cannot validate the key       | `BACKEND_PRIVATE_URL` is reachable and the key belongs to that installation.                                                    |
| File tools fail or reject a URL       | `PNEUMATIC_FILES_URL` matches the backend's `FILE_SERVICE_URL`; the internal storage address is reachable.                      |
| 429 responses                         | Per-key limit, backend/storage limits, or consent IP limits; check `TRUST_PROXY` if different users share the same apparent IP. |

## For Developers

Use Node.js **22.12+** (Node 24 is used by the Docker image) and npm. Run from the repository root:

```bash
cd mcp
npm ci
openssl rand -hex 32
mkdir -p .state
touch .state/replay.json
```

Create `mcp/.env`, pasting the generated secret as `TOKEN_SECRET`:

```dotenv
BACKEND_PRIVATE_URL=http://localhost:8001
PNEUMATIC_FILES_URL=http://localhost/files
FRONTEND_URL=http://localhost
PNEUMATIC_API_KEY=
MCP_TRANSPORT=http
HOST=127.0.0.1
PUBLIC_URL=http://localhost:3000
TOKEN_SECRET=<output of openssl rand -hex 32>
OAUTH_REPLAY_FILE=./.state/replay.json
OAUTH_ALLOWED_REDIRECT_HOSTS=claude.ai,claude.com,www.cursor.com,localhost,127.0.0.1,[::1]
TRUST_PROXY=loopback,uniquelocal
```

The example targets a local Pneumatic stack: API at `http://localhost:8001`, web app at `http://localhost`, files at `http://localhost/files`, connector at `http://localhost:3000`. Change these addresses for another installation. Keep the existing replay file on subsequent starts.

Start with file watching and explicit env loading:

```bash
node --env-file=.env --import tsx --watch src/index.ts --http
```

Or build and start:

```bash
npm run build
node --env-file=.env dist/index.js --http
```

### Local stdio client

Set `PNEUMATIC_API_KEY` in `mcp/.env` and build the server. Configure the client to launch `node` with the absolute env-file and entrypoint paths. In clients using the `mcpServers` format:

```json
{
  "mcpServers": {
    "pneumatic": {
      "command": "node",
      "args": [
        "--env-file=/absolute/path/to/pneumaticworkflow/mcp/.env",
        "/absolute/path/to/pneumaticworkflow/mcp/dist/index.js",
        "--stdio"
      ]
    }
  }
}
```

`--stdio` overrides the example's `MCP_TRANSPORT=http`; no HTTP secret or ledger is needed. Use your client's equivalent command/arguments settings if its configuration format differs. Protocol messages go to stdout; logs go to stderr.

### Verification

Run checks from `mcp/`:

```bash
npm run check
npm run build
```

`npm run check` runs `npm run lint` (formatting check, oxlint, typecheck) and then `npm test`. `npm run lint:fix` applies formatting and autofixable lint rules.

Tests use the fake API in `test/fakePneumatic.ts` and MCP client helpers in `test/harness.ts`. Add tools in `src/tools/`, assign their group in `src/tools/index.ts`, supply a title and annotations, and cover the behavior through the harness. `test/catalog.test.ts` validates catalog metadata; `test/http.test.ts` covers HTTP and OAuth.

For checks against a real installation, set `PNEUMATIC_API_KEY` in the local `.env`:

```bash
node --env-file=.env --import tsx scripts/smoke.ts
SMOKE_WRITES=yes node --env-file=.env --import tsx scripts/smoke-write.ts
```

The first script reads ten API endpoints. The second creates and changes data and attempts cleanup; use an admin key from a disposable account and check that the test workflow and template were removed. Before release, verify client consent, a read and write call, file upload/download, reconnect after restart, and rejection of a revoked key after five minutes.

### Directory publication

The maintained hosted endpoint and listing fields are in [distribution/listing.json](distribution/listing.json). These files describe that deployment; custom installations use their own addresses and policies. Keep the listing, [remote client configuration](distribution/mcp.json), [registry manifest](distribution/server.json) and deployed server version synchronized. A committed [PNG icon](distribution/icon.png) is included.

| Destination                                                                           | Prepared material                                                                                                                                                                   | Submission after deployment                                                                                                                                                                                       |
| ------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [Claude Connectors Directory](https://claude.com/docs/connectors/building/submission) | `listing.json`: descriptions, use cases, authentication, documentation/privacy/support links and reviewer setup.                                                                    | Open [the developer portal](https://claude.ai/directory/manage), choose **MCP connector**, and fill the fields from the listing. Supply the responsible contact and reviewer credentials privately in the portal. |
| [Cursor Marketplace](https://cursor.com/docs/reference/plugins#submitting-a-plugin)   | [Repository marketplace manifest](../.cursor-plugin/marketplace.json) selects `mcp/`; [plugin manifest](.cursor-plugin/plugin.json) includes the remote MCP configuration and icon. | Submit the public repository at [Cursor Marketplace](https://cursor.com/marketplace/publish) after testing the plugin locally.                                                                                    |
| [MCP Registry](https://modelcontextprotocol.io/registry/quickstart)                   | `distribution/server.json`, namespace `io.github.pneumaticapp/pneumatic`, remote Streamable HTTP endpoint.                                                                          | Authenticate as a publisher authorized for the `pneumaticapp` GitHub namespace, validate, then publish the manifest. A remote-only server needs no npm package.                                                   |
| Other MCP directories                                                                 | Reuse `listing.json`, the README and icon.                                                                                                                                          | Complete each directory's form; update existing submissions rather than creating duplicates.                                                                                                                      |

From `mcp/`, using the official [MCP publisher](https://github.com/modelcontextprotocol/registry/tree/main/docs/reference/cli):

```bash
mcp-publisher validate distribution/server.json
mcp-publisher login github
mcp-publisher publish distribution/server.json
```

Before submitting:

1. Deploy the selected version at the endpoint in `listing.json`. Set `PUBLIC_URL` (or root `MCP_PUBLIC_URL`) to its origin; keep `FRONTEND_URL` pointing at the web app. The bundled nginx templates serve the configured app hostname; a separate MCP hostname needs its own DNS, TLS and proxy routing.
2. Merge the documentation, icon and manifests into the public default branch. Open every listing URL without signing in; these GitHub URLs only work after merge. Confirm the hosted privacy policy and support contact apply to this deployment.
3. Verify unauthenticated MCP 401 and OAuth metadata on the public origin, then connect from the target clients. Exercise every exposed tool with a populated disposable account; test file transfers, denied permissions and revoked keys. Local automated tests do not replace this client/deployment check.
4. Prepare the reviewer account described in `listing.json`; enter its credentials only in the portal. Confirm the publishing account has the required directory and registry permissions, and accept the applicable terms when submitting.

The files are submission materials, not evidence of approval or an already published listing.
