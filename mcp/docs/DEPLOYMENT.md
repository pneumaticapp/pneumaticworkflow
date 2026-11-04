# Deploying the Pneumatic connector

How to host the connector in `http` mode for a team, so Claude.ai, Claude Desktop and remote Claude Code can use it. Every variable is listed in [Configuration](../README.md#configuration); logs and metrics are described in [Operations](../README.md#operations).

The shared server uses OAuth: each user supplies their own Pneumatic API key on the consent page. **Do not set `PNEUMATIC_API_KEY` on the shared server.** Run **one instance**: the replay ledger and upload links live in one process (see [Architecture](../README.md#architecture) for what replicas would need).

## With Pneumatic docker compose

A self-hosted Pneumatic installation already contains the connector (`mcp/` of the Pneumatic repository) as the `mcp` service of `docker-compose.yml`. It is off by default.

1. In the Pneumatic `.env`, set `MCP_ENABLED=true`. `start.sh` then adds the `mcp` compose profile. When running `docker compose` by hand, enable the profile yourself: `COMPOSE_PROFILES=mcp` (comma-separated with a `logs-*` profile) or `--profile mcp`. Setting `MCP_ENABLED` back to `false` makes `start.sh` remove the connector container; by hand, run `docker compose --profile mcp rm -sf mcp`.
2. Optionally set `MCP_TOKEN_SECRET` (at least 32 characters, `openssl rand -hex 32`); it defaults to `DJANGO_SECRET_KEY`. Changing it later signs every user out. `MCP_RATE_LIMIT_PER_MINUTE`, `MCP_TOOLSETS`, `MCP_READ_ONLY` and `MCP_LOG_LEVEL` map to the variables in [Configuration](../README.md#configuration).
3. Start Pneumatic as usual (`./start.sh`). Nothing else is needed:
   - nginx serves the connector on the web app origin: the MCP endpoint is `FRONTEND_URL/mcp`, and `/authorize`, `/token`, `/register`, `/upload/` and `/.well-known/oauth-*` go to the connector as well. Without the profile these paths answer 502 and the rest of Pneumatic is unaffected;
   - `PUBLIC_URL` and `PNEUMATIC_APP_URL` follow `FRONTEND_URL`, `PNEUMATIC_FILES_URL` follows `FILE_SERVICE_URL`; API and storage calls go over the internal network (`BACKEND_PRIVATE_URL`, `PNEUMATIC_FILES_INTERNAL_URL`);
   - the replay ledger lives in the `mcp-state` volume. The image creates it only when the volume is empty (`OAUTH_REPLAY_CREATE_IF_EMPTY=true`, set by the Pneumatic compose files); if other state is there but the ledger is gone, the connector refuses to start as described in step 2 below. Keep the volume on upgrades: removing it (for example, `docker compose down -v`) re-enables spent tokens until they expire.
4. Claude.ai reaches the connector only over HTTPS (`SSL=yes`); plain HTTP works only for clients on the same machine at `http://localhost/mcp`. With plain HTTP on any other address the connector refuses to start.

The rest of this guide covers running the connector on its own, next to Pneumatic Cloud or another installation.

## Requirements

- A host with Docker (or Node.js 20.19+ / 22.12+ to run `dist/index.js` directly) and a persistent directory for the replay ledger.
- A public DNS name for the connector (for example, `mcp.example.com`) and a TLS-terminating reverse proxy in front of it. Claude.ai needs HTTPS.
- Outbound access from the container to the Pneumatic API and file storage URLs below.
- Memory: plan for a 512 MB limit. Idle usage is small, but MCP requests may carry up to 16 MB and the upload page buffers up to 4 files of 25 MiB at once.

## URLs to set

| Variable              | Value                                                                                                | Used by                                                         |
| --------------------- | ---------------------------------------------------------------------------------------------------- | --------------------------------------------------------------- |
| `PUBLIC_URL`          | The connector's own public origin, e.g. `https://mcp.example.com`                                    | OAuth metadata, links to the consent and upload pages           |
| `PNEUMATIC_API_URL`   | Any backend URL **reachable from the container**; an internal address is fine                        | Server-side API calls only                                      |
| `PNEUMATIC_FILES_URL` | **Exactly** the backend's `FILE_SERVICE_URL` (the public file URL), and reachable from the container | Uploads, downloads; `download_file` accepts only links under it |
| `PNEUMATIC_APP_URL`   | Public web app URL; derived from `PNEUMATIC_FILES_URL` when it ends with `/files`                    | `webUrl` links shown to users                                   |

- **Pneumatic Cloud:** leave `PNEUMATIC_API_URL`, `PNEUMATIC_FILES_URL` and `PNEUMATIC_APP_URL` unset; the defaults point to `api.pneumatic.app` and `my.pneumatic.app`.
- **Self-hosted Pneumatic:** set `PNEUMATIC_FILES_URL` to the `FILE_SERVICE_URL` from the Pneumatic `.env` (for example, `https://pneumatic.example.com/files`). Pneumatic rejects file links that do not start with it. `localhost` URLs do not work inside a container: if Pneumatic runs on the same host, attach the connector to Pneumatic's Docker network and use `http://pneumatic-nginx` (the backend's `BACKEND_PRIVATE_URL` in the standard Pneumatic `docker-compose.yml`) as `PNEUMATIC_API_URL`, and make sure the public files hostname resolves from the container (DNS or `extra_hosts`).

## Steps

1. **Secrets and settings.** Generate `TOKEN_SECRET` **once** with `openssl rand -hex 32` and keep it in a secret manager or a restricted file outside the repository (for example, `/etc/pneumatic-connector/connector.env`, mode `0600`):

   ```dotenv
   MCP_TRANSPORT=http
   HOST=0.0.0.0
   PORT=3000
   PUBLIC_URL=https://mcp.example.com
   PNEUMATIC_API_URL=https://api.pneumatic.app
   PNEUMATIC_FILES_URL=https://my.pneumatic.app/files
   TOKEN_SECRET=<generated-secret>
   OAUTH_REPLAY_FILE=/state/replay.json
   OAUTH_ALLOWED_REDIRECT_HOSTS=claude.ai,claude.com
   # Optional: LOG_LEVEL=info, METRICS_TOKEN=<random 16+ chars>, TOOLSETS=core,files, READ_ONLY=false
   ```

   Replace the placeholder with the generated value; do not put shell commands in the env file. Add other trusted client redirect hosts only if needed (for local clients, `localhost,127.0.0.1,[::1]`). Do not use `*` in production. Changing `TOKEN_SECRET` later signs every user out.

2. **Ledger directory (fresh installation only).** Create a directory writable by the container's `node` user (UID 1000) and an empty ledger. The server refuses to start without the file, so that a lost volume cannot silently re-enable spent tokens. On upgrades keep the existing file; never run the `install /dev/null` command on it.

   ```bash
   sudo install -d -m 0700 -o 1000 -g 1000 /var/lib/pneumatic-connector
   sudo install -m 0600 -o 1000 -g 1000 /dev/null /var/lib/pneumatic-connector/replay.json
   ```

3. **Start the container.** Build the image from `mcp/` of the Pneumatic repository, or use the published image `pneumaticworkflow/pneumatic-mcp` (`stable` with each Pneumatic release, `latest` from `master`); in the examples below replace `build: .` (or `docker build`) with that image. The examples bind the HTTP port to loopback because the TLS proxy runs on the same host; if it runs elsewhere, expose port 3000 only on a private network. The image runs as a non-root user and has a Docker health check on `GET /healthz`.

   With Docker Compose (`compose.yaml` in `mcp/` of a clone of the Pneumatic repository):

   ```yaml
   services:
     pneumatic-connector:
       build: .
       image: pneumatic-connector:local
       restart: unless-stopped
       env_file: /etc/pneumatic-connector/connector.env
       volumes:
         - /var/lib/pneumatic-connector:/state
       ports:
         - 127.0.0.1:3000:3000
       mem_limit: 512m
       # Self-hosted Pneumatic on the same host: join its network (docker network ls shows the name).
       # networks: [pneumatic]
   # networks:
   #   pneumatic:
   #     external: true
   #     name: pneumatic_pneumatic
   ```

   ```bash
   docker compose up -d --build
   ```

   Or with plain Docker:

   ```bash
   docker build -t pneumatic-connector:0.1.0 .
   docker run -d --name pneumatic-connector --restart unless-stopped \
     --env-file /etc/pneumatic-connector/connector.env \
     -v /var/lib/pneumatic-connector:/state \
     -p 127.0.0.1:3000:3000 --memory 512m \
     pneumatic-connector:0.1.0
   ```

4. **Reverse proxy.** Forward **all paths** of the origin (`/mcp`, `/authorize`, `/token`, `/register`, `/.well-known/*`, `/upload/*`) and keep the original `Host` header: requests whose host is not the `PUBLIC_URL` host (or loopback) get 403. Allow bodies of at least 32 MB (MCP requests up to 16 MB, uploads up to 25 MiB) and disable buffering for streamed MCP responses. Example Nginx configuration (supply and renew the TLS certificate separately):

   ```nginx
   server {
       listen 443 ssl;
       server_name mcp.example.com;
       ssl_certificate /etc/letsencrypt/live/mcp.example.com/fullchain.pem;
       ssl_certificate_key /etc/letsencrypt/live/mcp.example.com/privkey.pem;
       client_max_body_size 32m;

       location / {
           proxy_pass http://127.0.0.1:3000;
           proxy_http_version 1.1;
           proxy_set_header Host $host;
           proxy_set_header X-Forwarded-Proto $scheme;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_buffering off;
           proxy_read_timeout 300s;
       }
   }
   ```

   `TRUST_PROXY` (default: loopback and private networks) must cover the proxy's address so per-IP limits see real client IPs.

5. **Check the public endpoints:**

   ```bash
   curl -fsS https://mcp.example.com/healthz
   curl -fsS https://mcp.example.com/.well-known/oauth-protected-resource/mcp
   curl -fsS https://mcp.example.com/.well-known/oauth-authorization-server
   curl -i -X POST https://mcp.example.com/mcp \
     -H 'Content-Type: application/json' --data '{}'
   ```

   Health returns `{"status":"ok"}`. The metadata must contain your public HTTPS URLs. The unauthenticated `/mcp` request must return **401** with a `WWW-Authenticate` header pointing to protected-resource metadata. These checks do not test Pneumatic connectivity: add the connector in Claude ([Claude.ai](../README.md#claudeai-custom-connector-remote), [Claude Code](../README.md#claude-code)) with a real key and ask "who am I in Pneumatic?" (`get_current_user`), then attach a file to a task to check the storage URL. [manual-checklist.md](manual-checklist.md) has the full release checklist.

## Upgrades, backups and monitoring

- **Upgrade:** pull the new version and run `docker compose up -d --build` (or rebuild and recreate the container with the same env file and volume). Users stay connected as long as `TOKEN_SECRET` and the ledger are kept. In-flight requests finish on `SIGTERM` (up to 10 seconds); pending upload links are lost.
- **Back up** `TOKEN_SECRET`. The ledger is not worth restoring from a backup: an old copy forgets tokens spent since then. If the ledger is lost, rotate `TOKEN_SECRET` (users connect again) and create a new empty file.
- **Monitor** the Docker health status (`/healthz` returns **503** after a ledger write failure until the next token request rewrites it; check disk space and permissions), the JSON logs on stderr (`docker logs`), and optionally Prometheus metrics at `/metrics` with `METRICS_TOKEN` (see [Operations](../README.md#operations)).

## Troubleshooting

| Symptom                                                                           | Likely cause                                                                                                        |
| --------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| Container exits with `Configuration error` in the logs                            | A missing or invalid variable; the message names it (for example, the ledger file does not exist)                   |
| `403` on every request through the proxy                                          | The proxy does not pass the original `Host`, or `PUBLIC_URL` has a different hostname                               |
| Claude shows an OAuth error before the consent page                               | The client's redirect host is not in `OAUTH_ALLOWED_REDIRECT_HOSTS`, or the proxy does not forward `/.well-known/*` |
| Consent page: "Could not reach Pneumatic to verify the key"                       | The container cannot reach `PNEUMATIC_API_URL` (DNS, firewall, `localhost` inside a container)                      |
| Consent page rejects a key that works in Pneumatic                                | `PNEUMATIC_API_URL` points to another Pneumatic instance, e.g. the Cloud default for a self-hosted key              |
| `413` when uploading or with long inputs                                          | The proxy's body limit (`client_max_body_size`) is below 32 MB                                                      |
| File tools return `not_configured`                                                | `PNEUMATIC_FILES_URL` is unset for a self-hosted backend                                                            |
| Pneumatic rejects uploaded file links, or `download_file` refuses Pneumatic links | `PNEUMATIC_FILES_URL` differs from the backend's `FILE_SERVICE_URL`                                                 |
| Many users hit `429` together, or the consent form blocks everyone                | `TRUST_PROXY` does not trust the proxy, so all clients appear to share the proxy's IP                               |
