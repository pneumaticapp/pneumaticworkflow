# Audit journal deployment

For dev/staging and production, with Loki/Grafana or Elasticsearch/Kibana.
`ansible/` paths belong to `pneumatic-deploy-config`; `logging/` and
`otel-collector/` belong to `pneumaticworkflow`. Keep actual addresses, keys
and passwords in deployment settings. Replace `<env>`, `<label>` and release placeholders.

| Target | `<env>` | Backend `ENVIRONMENT` / `<label>` | Files `CONFIG` |
|---|---|---|---|
| Dev/staging | `staging` | `Staging` | `Production` |
| Production | `prod` | `Production` | `Production` |

## Prepare and choose a stack

Use a tested application release, backups and previous release refs. Redis
server must support `XAUTOCLAIM` (6.2+); infrastructure handles upgrades.
Prepare trusted SSH/Git access, Docker, Ansible Python and disk capacity.
Logging jobs use `docker compose`; backend/files jobs use `docker-compose`.
Ensure the required command is available on each host.
Allow private backend-to-storage traffic and trusted access to the UI.

| Stack | `LOGS_BACKEND` | Storage / UI ports | Current Ansible support |
|---|---|---|---|
| Loki + Grafana | `otlp` | 3100 / 3000 | Implemented for staging; production needs collector configuration below |
| Elasticsearch + Kibana | `elasticsearch` | 9200 HTTPS / 5601 HTTPS | Manual setup exists; Ansible changes below are required |

Use separate storage/data for each environment. Choose one stack per environment.

## Configure deploy-config

Keep existing `app` repository/SSH settings and use the selected environment's
hosts and release ref. Add only missing settings:

| File | Change |
|---|---|
| `ansible/environments/pneumatic/logging/<env>/inventory.yml` | Logging host, SSH/interpreter; retain staging's groups |
| `ansible/environments/pneumatic/logging/<env>/vars.yml` | `app` metadata and the selected storage stack's settings |
| `ansible/environments/pneumatic/backend/<env>/vars.yml` | Journal settings below |
| `ansible/environments/pneumatic/files/<env>/vars.yml` | Shared journal settings below |
| `ansible/roles/app_render_dockerfiles/templates/pneumatic/backend/<env>/docker-compose.yml.j2` | Conditional collector, `otel_env`, internal network and external persistent queue volume |
| `ansible/roles/otel_collector_init/tasks/` | Prepare the selected mode's configs/queue before `app_reload`; enable the required environment/mode |

| Dictionary | Common settings |
|---|---|
| `backend_env` | Selected `LOGS_BACKEND`, `LOGS_OTLP_ENDPOINT` (internal collector), positive `LOGS_STREAM_MAXLEN` and `LOGS_CONSUMER_BATCH_SIZE` |
| `redis_env` | `LOGS_REDIS_URL` (dedicated events database shared by backend/worker/beat/files) |
| `file_service_env` | Same `LOGS_BACKEND`, `LOGS_REDIS_URL` and `LOGS_STREAM_MAXLEN`; files needs no collector |

### Loki + Grafana

- `logging_env`: `LOKI_BIND`, `LOKI_PORT`, `GRAFANA_BIND`, `GRAFANA_PORT`,
  `GRAFANA_ADMIN_USER`, `LOGS_RETENTION_PERIOD`.
- `otel_env`: `LOGS_OTLP_EXPORT_ENDPOINT` (private Loki, ending in `/otlp`)
  and `LOGS_OTLP_EXPORT_AUTH` (empty for this Loki).
- Collector: copy staging's service/volume into the required template; load
  `base.yaml` and `backend-otlp.yaml` from `pneumaticworkflow/otel-collector/`,
  followed by the `durable-otlp.yaml` override rendered by the deploy-config role.
  Change the current staging-only role condition to include `prod` when needed.
- `logging_deploy` generates/preserves the initial Grafana password in the
  logging server's `logging/grafana/.env`; keep that file and the data volumes.

### Elasticsearch + Kibana

- On storage, follow [the manual setup](README.md#elasticsearch--kibana): copy
  `elasticsearch.env.example` to `.env`, set its values, create certificates,
  start Compose and bootstrap roles, data stream, retention, snapshots and
  the collector API key.
- `otel_env`: `LOGS_ELASTICSEARCH_URL`, `LOGS_ELASTICSEARCH_API_KEY`,
  `LOGS_ELASTICSEARCH_CA_FILE`, `LOGS_ELASTICSEARCH_INDEX` (match `ES_DATA_STREAM`).
  Copy the storage CA into the collector config and mount it at
  `LOGS_ELASTICSEARCH_CA_FILE`; the URL hostname must match the certificate.
- Extend collector preparation and Compose conditions to `elasticsearch`:
  load `base.yaml` + `backend-elasticsearch.yaml` from
  `pneumaticworkflow/otel-collector/`, pass `otel_env` and mount the
  persistent queue at `/var/lib/otelcol` with collector write permissions.
  Keep receiver ports internal; do not load the Loki durable override.
- To automate storage, extend `ansible/roles/logging_deploy/tasks/main.yml`
  to select `logging/elasticsearch`, preserve secrets/certificates and run its
  setup scripts. The current role always deploys `logging/grafana`.
- Rotate the API key before expiry. For planned Elasticsearch restarts, stop
  the collector first and resume it once storage responds; the supplied
  exporter can drop events on transport errors.

## Deploy and verify

Existing logging Jenkins command (**Loki only**); SCM selects deploy-config,
while `branch` selects the application release:

```bash
ansible-playbook ansible/logging.yml -v -i "ansible/environments/pneumatic/logging/<env>/inventory.yml" -e "env=<env> branch=<application-release-ref> project=pneumatic"
```

1. Deploy **storage -> backend/collector -> files**, using the same application
   ref and existing backend/files jobs after the required collector changes.
   Use the manual setup for Elasticsearch until its Ansible support is added.
2. Manually check storage/UI health and application/worker/beat/collector logs.
   Jenkins SUCCESS confirms deploy commands; backend does not wait for storage
   readiness. Invalid settings, preparation and Docker errors still fail startup/deploy.
3. Perform sign-in, a backend action and file upload/download. Find both
   services' events in Grafana Explore (below) or Kibana Discover; first create
   a Kibana data view matching `ES_DATA_STREAM` as an administrator.
   Verify the environment and timestamps.

```logql
{service_name=~"pneumatic-.*", deployment_environment="<label>"}
```

## Disable, switch or roll back

Set files `LOGS_BACKEND` empty and redeploy; drain Redis/collector, then set
backend `LOGS_BACKEND` empty and redeploy. Preserve Redis, storage/queue volumes,
`.env`, certificates and encryption keys; prevent volume cleanup from deleting
unused queues/data. Switching stacks does not migrate existing history.
Check migration compatibility before deploying an older ref.
