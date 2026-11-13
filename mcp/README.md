# Pneumatic MCP server

## About

Connects compatible MCP clients to a Pneumatic installation using Streamable HTTP or stdio. Tools read and update tasks, workflows, templates, files, reports, users, groups and datasets through the Pneumatic API, with the permissions of the API key owner.

| Transport | Client connection                     | Authentication                                                                                                                  |
| --------- | ------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| HTTP      | Streamable HTTP at `<PUBLIC_URL>/mcp` | OAuth with PKCE: each user enters their API key on the consent page. A raw API key in `Authorization: Bearer <key>` also works. |
| stdio     | Client starts a local Node.js process | `PNEUMATIC_API_KEY` in the process environment.                                                                                 |

Create a key in your installation under **Integrations → Your API Keys → Create** (account owner or admin). The full key is shown once. To revoke access, delete the key there; HTTP key validation is cached for up to five minutes.

## Configuration

### Pneumatic Docker Compose

Edit the **repository-root `.env`** when using [docker-compose.yml](../docker-compose.yml), [docker-compose.src.yml](../docker-compose.src.yml) or `start.sh`. These files map installation settings to the connector's environment; `mcp/.env` is not read by the root Compose files.

| Root `.env` variable               | Default                                                                                   | Meaning                                                                                                                                                                                                                                               |
| ---------------------------------- | ----------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `MCP_ENABLED`                      | `false`                                                                                   | `start.sh` switch: `true` adds the `mcp` profile; `false` or empty removes an existing connector container. Other values fail startup. Docker Compose itself does not read this switch.                                                               |
| `COMPOSE_PROFILES`                 | Unset                                                                                     | For direct Compose commands, include `mcp` or use `--profile mcp`. Combine profiles on one comma-separated line, e.g. `logs-otlp,mcp`. With `start.sh`, use `MCP_ENABLED=true`; leaving `mcp` in this list while disabling `MCP_ENABLED` is an error. |
| `MCP_PUBLIC_URL`                   | `FRONTEND_URL`, falling back to `http://localhost`                                        | Overrides `PUBLIC_URL` when the MCP server has its own public HTTPS origin. Configure DNS/TLS and proxy routing for that origin separately.                                                                                                           |
| `MCP_OAUTH_ALLOWED_REDIRECT_HOSTS` | Empty: process defaults below                                                             | Overrides `OAUTH_ALLOWED_REDIRECT_HOSTS` with the full comma-separated callback hostname list for your clients.                                                                                                                                       |
| `MCP_TOKEN_SECRET`                 | `DJANGO_SECRET_KEY`; if both are empty/unset, `django_secret_django_secret_django_secret` | Maps to `TOKEN_SECRET`. Set a separate random value of at least 32 characters, generated once with `openssl rand -hex 32`. Changing it invalidates OAuth tokens and client registrations.                                                             |
| `MCP_RATE_LIMIT_PER_MINUTE`        | `120`                                                                                     | Maps to `RATE_LIMIT_PER_MINUTE`: non-negative integer, MCP requests per API key per minute; `0` disables the limit.                                                                                                                                   |
| `MCP_TOOLSETS`                     | Empty: all tools                                                                          | Maps to `TOOLSETS`: comma-separated groups from the table below, or `all`.                                                                                                                                                                            |
| `MCP_READ_ONLY`                    | `false`                                                                                   | Maps to `READ_ONLY`: `true` hides tools that change data. Also accepts `yes`/`1` and `no`/`0`.                                                                                                                                                        |
| `MCP_LOG_LEVEL`                    | `info`                                                                                    | Maps to `LOG_LEVEL`: `debug`, `info`, `warn`, `error`, `off`. Logs are JSON lines on stderr.                                                                                                                                                          |

The connector reuses these existing installation settings:

| Root `.env` variable  | Default used by the MCP service | Connector variable and purpose                                                                                         |
| --------------------- | ------------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| `FRONTEND_URL`        | `http://localhost`              | Sets `PNEUMATIC_APP_URL` for web app links and supplies the fallback for `PUBLIC_URL` when `MCP_PUBLIC_URL` is unset.  |
| `BACKEND_PRIVATE_URL` | `http://pneumatic-nginx`        | Sets `PNEUMATIC_API_URL`: backend address reachable from the connector container.                                      |
| `FILE_SERVICE_URL`    | `http://localhost/files`        | Sets `PNEUMATIC_FILES_URL`: public file URL prefix; must match the backend's setting.                                  |
| `FILE_PORT`           | `8000`                          | Sets `PNEUMATIC_FILES_INTERNAL_URL` to `http://pneumatic-file-service:<FILE_PORT>` for storage requests inside Docker. |

The image sets `MCP_TRANSPORT=http`, `HOST=0.0.0.0` and `PORT=3000`. Compose sets `OAUTH_REPLAY_FILE=/state/replay.json` and `OAUTH_REPLAY_CREATE_ON_EMPTY_VOLUME=true`, and mounts `mcp-state` at `/state`. Other HTTP settings below keep their process defaults. To override a setting absent from the service's `environment`, add it with a Compose override file; putting it only in the root `.env` does not pass it into the container.

### Standalone process

Use [`.env.example`](.env.example) for a process running on the host. The following settings are read by the connector itself. Load a file explicitly with `node --env-file=.env`; `npm start` and `npm run dev` do not load it automatically. Variables already exported in the shell take precedence over the env file.

Set the addresses explicitly for your installation. The standalone configuration retains legacy hosted-service fallbacks (`DEFAULT_API_URL` and `DEFAULT_FILES_URL` in [src/config.ts](src/config.ts)); none of the examples below depend on them.

| Variable                       | Default when omitted                                                       | Meaning / value to supply                                                                                                                                                                         |
| ------------------------------ | -------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `PNEUMATIC_API_URL`            | `DEFAULT_API_URL` in [src/config.ts](src/config.ts)                        | Backend HTTP(S) base URL, e.g. `http://localhost:8001` on the host or `https://api.example.com` remotely. Do not append an API resource path.                                                     |
| `PNEUMATIC_FILES_URL`          | Unset for a custom API URL; `DEFAULT_FILES_URL` for the legacy default API | Set to the backend's `FILE_SERVICE_URL`, e.g. `https://app.example.com/files`. Used for returned links and download URL validation; required for uploads and downloads.                           |
| `PNEUMATIC_FILES_INTERNAL_URL` | Unset: requests use `PNEUMATIC_FILES_URL`                                  | Optional storage address reachable by the process, e.g. `http://pneumatic-file-service:8000` inside the Compose network. Requires `PNEUMATIC_FILES_URL`; returned links still use the public URL. |
| `PNEUMATIC_APP_URL`            | `PNEUMATIC_FILES_URL` with a final `/files` removed; otherwise unset       | Web app base URL for task, workflow and template links. Set explicitly if the file URL has another path; unset means no web app links in results.                                                 |
| `MCP_TRANSPORT`                | `stdio`                                                                    | `stdio` or `http`. Command-line `--http` / `--stdio` overrides it. The Docker image defaults to `http`.                                                                                           |
| `PNEUMATIC_API_KEY`            | Unset                                                                      | Required for stdio and the smoke scripts. HTTP requests supply a key per user, so leave it unset on a shared HTTP server.                                                                         |
| `TOOLSETS`                     | All groups                                                                 | Comma-separated names below, or `all`; empty also selects all. Unknown names fail startup.                                                                                                        |
| `READ_ONLY`                    | `false`                                                                    | `true`/`yes`/`1` exposes only read tools; `false`/`no`/`0` or empty permits writes.                                                                                                               |
| `LOG_LEVEL`                    | `info`                                                                     | `debug`, `info`, `warn`, `error`, `off`; invalid values fail startup.                                                                                                                             |

Backend, file and app URLs accept HTTP(S) without credentials, query strings or fragments; trailing slashes are removed. `localhost` inside a container refers to that container, not to the host.

| `TOOLSETS` group | Contents                                                                                                |
| ---------------- | ------------------------------------------------------------------------------------------------------- |
| `core`           | Tasks, workflows, template lookup/launch, comments, notifications, vacation, user/group/dataset lookup. |
| `files`          | Attachments, uploads and downloads; browser upload links require HTTP mode.                             |
| `design`         | Template creation, editing and the template library.                                                    |
| `analytics`      | Dashboard, highlights, workflow counts, step statistics and field-value reports.                        |
| `admin`          | User, group and dataset management; reassignment.                                                       |

### HTTP settings

These variables are ignored in stdio mode. `TOKEN_SECRET` and `OAUTH_REPLAY_FILE` are required for HTTP startup.

| Variable                       | Process default                                                 | Meaning / allowed values                                                                                                                                                                                                       |
| ------------------------------ | --------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `HOST`                         | `127.0.0.1`                                                     | Listen address; the Docker image uses `0.0.0.0`.                                                                                                                                                                               |
| `PORT`                         | `3000`                                                          | Integer from `1` to `65535`.                                                                                                                                                                                                   |
| `PUBLIC_URL`                   | `http://localhost:<PORT>`                                       | Connector origin used in OAuth metadata, consent and upload links, e.g. `https://mcp.example.com`. No path, query, fragment or credentials; HTTPS required except for `localhost`, `127.0.0.1`, `[::1]`. Do not append `/mcp`. |
| `TOKEN_SECRET`                 | Unset                                                           | At least 32 characters. Generate once with `openssl rand -hex 32` and keep across restarts.                                                                                                                                    |
| `OAUTH_REPLAY_FILE`            | Unset                                                           | Path to an existing, writable persistent file containing spent OAuth token identifiers. Compose uses `/state/replay.json`; local development uses `./.state/replay.json`.                                                      |
| `OAUTH_ALLOWED_REDIRECT_HOSTS` | `claude.ai,claude.com,www.cursor.com,localhost,127.0.0.1,[::1]` | Comma-separated callback hostnames, without schemes, paths or ports. Set the full list when adding another client. `*` permits any host.                                                                                       |
| `RATE_LIMIT_PER_MINUTE`        | `120`                                                           | Non-negative integer, MCP requests per API key per minute; `0` disables this limit. Consent failures have a separate fixed limit of 10 per client IP per minute.                                                               |
| `TRUST_PROXY`                  | `loopback,uniquelocal`                                          | Trusted reverse proxy addresses/subnets, hop count, or `true`/`false`. Determines which `X-Forwarded-For` values are trusted for client IP limits. Match your proxy network.                                                   |
| `METRICS_TOKEN`                | Unset: `/metrics` disabled                                      | At least 16 characters; enables Prometheus metrics with `Authorization: Bearer <METRICS_TOKEN>`.                                                                                                                               |

`OAUTH_REPLAY_CREATE_ON_EMPTY_VOLUME` is a **Docker entrypoint** setting, not a Node.js setting. Unset disables creation; exactly `true` creates the file named by `OAUTH_REPLAY_FILE` only if its directory exists and is empty. Compose enables it for a new `mcp-state` volume.

`PUBLIC_URL` and `PNEUMATIC_APP_URL` can differ: for example, `https://mcp.example.com` hosts the connector while `https://app.example.com` hosts the web app. Compose uses `FRONTEND_URL` for the app and, unless overridden by `MCP_PUBLIC_URL`, for the connector.

## Installation / Get started

### With the Pneumatic stack

Requires a configured Pneumatic installation and Docker Compose. Run commands from the repository root. For remote clients, configure HTTPS for the installation (`SSL=yes` with the bundled nginx) and set `FRONTEND_URL` and `FILE_SERVICE_URL` to your public addresses. HTTP is accepted only on loopback.

1. Generate a secret with `openssl rand -hex 32`. In the root `.env`, set `MCP_ENABLED=true` and `MCP_TOKEN_SECRET=<generated value>`. Paste the generated value, not the command.
2. Run `./start.sh`; select **From sources** to build this checkout. Alternatively, start directly with Compose:

   ```bash
   docker compose --profile mcp up -d --build
   ```

3. Check the connector:

   ```bash
   docker compose --profile mcp ps mcp
   docker compose --profile mcp logs --tail=50 mcp
   docker compose --profile mcp exec mcp wget -qO- http://127.0.0.1:3000/healthz
   curl -i -X POST https://mcp.example.com/mcp -H 'Content-Type: application/json' --data '{}'
   curl -fsS https://mcp.example.com/.well-known/oauth-authorization-server
   ```

   Replace `https://mcp.example.com` with `MCP_PUBLIC_URL` if set, otherwise `FRONTEND_URL`. Health returns `{"status":"ok"}`; unauthenticated `/mcp` returns **401** with `WWW-Authenticate`; OAuth metadata contains your public origin. These checks do not verify backend access: connect a client and call `get_current_user` next.

The bundled nginx forwards `/mcp`, `/authorize`, `/token`, `/register`, `/upload/` and `/.well-known/oauth-*` on the web app origin. `/healthz` and `/metrics` are accessible inside the connector container, not through these nginx routes. With the connector stopped, its nginx routes return 502.

To disable it through `start.sh`, set `MCP_ENABLED=false` and remove `mcp` from `COMPOSE_PROFILES`. With direct Compose commands, remove `mcp` from the enabled profiles and run `docker compose --profile mcp rm -sf mcp`. Disabling a profile alone does not stop an already running container.

### Standalone Docker

Run from `mcp/`. Copy `.env.example` to `.env`, then set `PNEUMATIC_API_URL`, `PNEUMATIC_FILES_URL` and `PNEUMATIC_APP_URL` to your installation's addresses. For Docker, set `HOST=0.0.0.0`, `PUBLIC_URL=https://mcp.example.com`, `TOKEN_SECRET` to a generated secret, and `OAUTH_REPLAY_FILE=/state/replay.json`. The API and storage addresses must be reachable from the container; use `PNEUMATIC_FILES_INTERNAL_URL` if the public storage address is not reachable there.

```bash
docker build -t pneumatic-mcp:local .
docker volume create pneumatic-mcp-state
docker run -d --name pneumatic-mcp --restart unless-stopped \
  --env-file .env \
  -e OAUTH_REPLAY_CREATE_ON_EMPTY_VOLUME=true \
  -v pneumatic-mcp-state:/state \
  -p 127.0.0.1:3000:3000 \
  pneumatic-mcp:local
```

Put a TLS reverse proxy in front of `127.0.0.1:3000`. Forward `/mcp`, `/authorize`, `/token`, `/register`, `/upload/` and `/.well-known/oauth-*` without rewriting their paths; preserve `Host`, set trusted forwarding headers, disable response buffering and allow request bodies of at least 26 MiB. The bundled [MCP locations](../nginx/includes/location_mcp.conf) and [proxy settings](../nginx/includes/proxy_to_mcp.conf) show these requirements. Keep upload-token paths out of access logs. `PUBLIC_URL` must match the externally reachable origin.

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

- `mcp-state` is a Docker named volume containing `/state/replay.json`: spent authorization codes, refresh-token identifiers and session revocations with expiry times. It contains no API keys or uploaded files. [Named volumes](https://docs.docker.com/engine/storage/volumes/) persist across container replacement and host restarts; a host-directory bind mount is not required.
- Keep the volume and `TOKEN_SECRET` on upgrades. `docker compose down -v` deletes the named volume. If the ledger is lost or restored from an older copy, rotate the secret before creating a new ledger; users must reconnect. Reusing the old secret with missing records allows spent tokens to be accepted again.

### Troubleshooting

| Symptom                               | Check                                                                                                                           |
| ------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| Startup reports `Configuration error` | The named variable in the log, secret length, replay file existence and write permissions.                                      |
| 403 through the proxy                 | Original `Host` is preserved and matches `PUBLIC_URL`; the origin is allowed.                                                   |
| OAuth fails before consent            | All OAuth paths are forwarded and the callback hostname is in `OAUTH_ALLOWED_REDIRECT_HOSTS`.                                   |
| Consent cannot validate the key       | `PNEUMATIC_API_URL` is reachable and the key belongs to that installation.                                                      |
| File tools fail or reject a URL       | `PNEUMATIC_FILES_URL` matches the backend's `FILE_SERVICE_URL`; the internal storage address is reachable.                      |
| 429 responses                         | Per-key limit, backend/storage limits, or consent IP limits; check `TRUST_PROXY` if different users share the same apparent IP. |

## For Developers

Use Node.js **22.12+** (Node 24 is used by the Docker image) and npm. Run from the repository root:

```bash
cd mcp
npm ci
cp .env.example .env
openssl rand -hex 32
mkdir -p .state
touch .state/replay.json
```

For this first local setup, paste the generated secret into `.env` as `TOKEN_SECRET`. The example targets a local Pneumatic stack: API at `http://localhost:8001`, web app at `http://localhost`, files at `http://localhost/files`, connector at `http://localhost:3000`. Change these addresses for another installation. Keep the existing replay file on subsequent starts.

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
npm run lint
npm run format:check
npm run typecheck
npm test
npm run build
```

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

1. Deploy the selected version at the endpoint in `listing.json`. Set `PUBLIC_URL` (or root `MCP_PUBLIC_URL`) to its origin; keep `PNEUMATIC_APP_URL` / `FRONTEND_URL` pointing at the web app. The bundled nginx templates serve the configured app hostname; a separate MCP hostname needs its own DNS, TLS and proxy routing.
2. Merge the documentation, icon and manifests into the public default branch. Open every listing URL without signing in; these GitHub URLs only work after merge. Confirm the hosted privacy policy and support contact apply to this deployment.
3. Verify unauthenticated MCP 401 and OAuth metadata on the public origin, then connect from the target clients. Exercise every exposed tool with a populated disposable account; test file transfers, denied permissions and revoked keys. Local automated tests do not replace this client/deployment check.
4. Prepare the reviewer account described in `listing.json`; enter its credentials only in the portal. Confirm the publishing account has the required directory and registry permissions, and accept the applicable terms when submitting.

The files are submission materials, not evidence of approval or an already published listing.
