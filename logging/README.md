# Pneumatic audit journal storage

The storage side of the Pneumatic audit journal: the services that keep the
user action events and let people search and chart them.

The application machine does not run anything from this directory. There the
backend and the file service write events into a Redis stream, and the
OpenTelemetry collector (`otel-collector/` in the root of the repository)
forwards them to the store named by `LOGS_BACKEND` in `.env`. While
`LOGS_ENABLE` is empty, `start.sh` asks whether to enable the journal, asks
for the store settings and starts the collector through the compose profile
`logs-otlp` or `logs-elasticsearch`; with the journal off, no collector runs.

```
application machine                                  storage machine
backend, file service -> Redis stream -> collector --OTLP/HTTP--> Loki <- Grafana         logging/grafana
                                                    --HTTPS------> Elasticsearch <- Kibana logging/elasticsearch
```

## Deployed to a separate server

The files of the `logging` directory are deployed to a separate server, the
storage machine, not to the machine that runs Pneumatic. Each stack has its own
compose file and its own `.env`, and neither is connected to the root
`docker-compose.yml` / `docker-compose.src.yml`. Run them on the storage
machine with `docker compose` from their own directory, manually or through
the deployment automation described below.

Put the `logging` directory on the storage machine (a checkout of the
repository or a copy of the directory). `logging/grafana` mounts
`../loki/loki-config.yaml`, so keep `grafana` and `loki` side by side.

## Staging and production deployment

See [the deployment guide](PRODUCTION.md) for environment selection, the
Loki/Grafana and Elasticsearch/Kibana variants, deploy-config changes,
deployment order, manual delivery checks and rollback. Keep actual addresses,
keys and passwords in deployment settings.

The current Ansible logging role deploys Loki/Grafana; Elasticsearch needs
the manual setup below and additional Ansible support described in the guide.
Check application readiness and event delivery manually after deployment;
backend deployment has no storage or collector readiness gate.

## Stacks

Pick one per installation, `LOGS_BACKEND` takes a single value.

| Directory | Services | What it is for | `LOGS_BACKEND` |
|---|---|---|---|
| `grafana/` + `loki/` | Loki, Grafana | Journal in Loki, 10 provisioned dashboards (the home one is Project overview, plus event search, critical events, accounts, workflows, pipeline health and others) and 5 alert rules (failed sign-ins, refused and cross-account file downloads, a pipeline that delivers nothing) | `otlp` |
| `elasticsearch/` | Elasticsearch, Kibana | Journal in an Elasticsearch data stream with an index lifecycle (retention), daily snapshots, a write-only API key for the collector and a read-only account for people in Kibana | `elasticsearch` |

`LOGS_BACKEND=otlp` also works with any other OTLP/HTTP receiver (an
observability stack of your own); nothing from this directory is needed then.

Every record carries the actor e-mail, IP address and user agent, and both
stacks show the journal of every account in the installation: keep Loki and
Elasticsearch reachable from the application machine only, and Grafana and
Kibana behind your own access control.

## Configuration

The variables below belong to the **repository-root `.env` of the application
machine**, read by [docker-compose.yml](../docker-compose.yml),
[docker-compose.src.yml](../docker-compose.src.yml) and `start.sh`; `default.env`
lists them all. The storage machine has its own settings, see
`grafana/grafana.env.example` and `elasticsearch/elasticsearch.env.example`.
The **Mode** column shows the `LOGS_BACKEND` value a variable applies to.
Defaults apply when a variable is omitted.

| Variable                       | Mode            | Default                              | Meaning / example                                                                                                                                                                                                                                                                                              |
| ------------------------------ | --------------- | ------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `LOGS_ENABLE`                  | All             | Unset: not decided                   | `yes` or `no`, the answer to the `start.sh` question about the journal. While empty, `start.sh` asks it and fills in this variable, `LOGS_BACKEND` and the settings of the chosen mode. Change it to empty to answer again.                                                                                    |
| `LOGS_BACKEND`                 | All             | Unset: journal off                   | `otlp` sends events to an OTLP/HTTP receiver (Loki of `grafana/` or a stack of your own), `elasticsearch` to the store of `elasticsearch/`. Unset or empty: no collector runs and nothing is written to Redis. Set by the `start.sh` dialog.                                                                   |
| `LOGS_OTLP_ENDPOINT`           | All             | `http://otel-collector:4318`         | Address of the bundled collector the backend sends batches to. Change it only for a collector of your own.                                                                                                                                                                                                     |
| `LOGS_STREAM_MAXLEN`           | All             | `250000`                             | Events the Redis buffer keeps before the oldest are dropped. Also its memory budget: plan with 1 KB per event, so the default takes ~250 MB plus 10 MB of dead letter. Sets how long the collector may be down without losses: ~69 hours at 1 event/s, ~7 hours at 10/s, ~42 minutes at 100/s.                 |
| `LOGS_CONSUMER_BATCH_SIZE`     | All             | `1000`                               | Events in one POST to the collector. A batch refused with `413` (body too large for the collector or a proxy in front of it) goes to the dead letter; lower the value then.                                                                                                                                    |
| `LOGS_OTLP_EXPORT_ENDPOINT`    | `otlp`          | Unset                                | OTLP/HTTP receiver URL on the storage machine, e.g. `http://<storage machine>:3100/otlp` for Loki of `grafana/`.                                                                                                                                                                                               |
| `LOGS_OTLP_EXPORT_AUTH`        | `otlp`          | Unset                                | Whole `Authorization` header value, e.g. `Bearer <token>` or `Basic <base64>`. Sent even when empty, see `otel-collector/backend-otlp.yaml`; Loki of `grafana/` needs none.                                                                                                                                    |
| `LOGS_ELASTICSEARCH_URL`       | `elasticsearch` | Unset                                | Store address, HTTPS only, e.g. `https://es.pneumatic.internal:9200`. The host must be one of the names in `ES_CERT_DNS` of the storage machine.                                                                                                                                                               |
| `LOGS_ELASTICSEARCH_API_KEY`   | `elasticsearch` | Unset                                | Collector API key printed by `elasticsearch/scripts/bootstrap.sh` or `rotate-api-key.sh`. Its role can only append to the journal, and it expires after `ES_API_KEY_EXPIRATION`; rotation is this line plus a collector restart. Preferred over login and password.                                            |
| `LOGS_ELASTICSEARCH_USER`      | `elasticsearch` | Unset                                | Elasticsearch account login, an alternative to the API key for a store without API keys. Set the key or the login and password, never both.                                                                                                                                                                    |
| `LOGS_ELASTICSEARCH_PASSWORD`  | `elasticsearch` | Unset                                | Password of `LOGS_ELASTICSEARCH_USER`.                                                                                                                                                                                                                                                                         |
| `LOGS_ELASTICSEARCH_CA_FILE`   | `elasticsearch` | `/etc/otel/es-ca.crt`                | CA certificate of the store inside the collector: copy `elasticsearch/certs/ca/ca.crt` from the storage machine to `otel-collector/es-ca.crt`, that directory is already mounted. Empty means the system certificate store, for a publicly trusted certificate.                                                |
| `LOGS_ELASTICSEARCH_INDEX`     | `elasticsearch` | `logs-pneumatic.events.otel-default` | Data stream the events are written to. Keeps the form `logs-<dataset>.otel-<namespace>` and matches `ES_DATA_STREAM` and `ES_INDEX_PATTERN` of the storage machine: the index template, retention policy and writer role are bound to it.                                                                      |
| `LOGS_ELASTICSEARCH_QUEUE_DIR` | `elasticsearch` | `/var/lib/otelcol/queue`             | Collector disk queue of undelivered batches, in the `./otel-queue` directory next to the compose files. No reason to change it.                                                                                                                                                                               |
| `COMPOSE_PROFILES`             | —               | Unset                                | Rewritten by `start.sh` from `LOGS_ENABLE`, `LOGS_BACKEND` and `MCP_ENABLE` whenever one of its dialogs runs; edit it by hand only without `start.sh`. `logs-otlp` or `logs-elasticsearch` starts the collector; without it an enabled journal piles events up in the buffer until `LOGS_STREAM_MAXLEN` drops the oldest. One line for all profiles, e.g. `logs-otlp,mcp`. |

The buffer is a Redis stream in db4 of the shared Redis, opened with
`REDIS_PASSWORD`. It holds the only copy of an event until the collector takes
it, and that Redis keeps RDB snapshots only, so a crash costs at most ~20
seconds of events. To size `LOGS_STREAM_MAXLEN`, check the rate of workflow
events, the bulk of the journal, over the last day:

```sql
select count(*) / 86400.0 from processes_workflowevent
where created > now() - interval '1 day';
```

The file service writes into the same journal (uploads, downloads and refused
downloads) and reads `LOGS_BACKEND`, `REDIS_PASSWORD` and `LOGS_STREAM_MAXLEN`
from the same `.env`; it has nothing to configure separately. On an upgrade,
deploy the backend first, then the file service: the backend declares the file
event types, and a file service ahead of it files its records under the other
category with the file name exposed.

## Loki + Grafana

On the storage machine, in `logging/grafana`:

1. Create the settings file and keep it `600` (it is in `.gitignore`):

   ```
   cp grafana.env.example .env
   ```

2. Set `GRAFANA_ADMIN_PASSWORD` (required, the stack does not start without
   it; for example `openssl rand -base64 24`). It is applied only when the
   `grafana-data` volume is created; later it is changed with
   `docker exec pneumatic-grafana grafana cli admin reset-admin-password NEW`.
3. Set `LOKI_BIND` to an interface only the application machine reaches (a
   private network, a VPN, a firewall rule). Loki has no authentication of its
   own; never bind it to `0.0.0.0` on a public host. The default `127.0.0.1`
   only fits a stack on the same machine as the application.
4. Optional: `LOKI_PORT` (3100), `GRAFANA_BIND` / `GRAFANA_PORT`
   (`127.0.0.1:3000`, put a reverse proxy with TLS in front before opening it
   to a network), `GRAFANA_ADMIN_USER` (`admin`), `GRAFANA_HOME_DASHBOARD`,
   `LOGS_RETENTION_PERIOD` (`365d`).
5. Start the stack:

   ```
   docker compose up -d
   ```

   Grafana provisions the Loki datasource, the dashboards and the alert rules
   from `./provisioning` on every start. Alert thresholds are edited in
   `provisioning/alerting/rules.yaml` (lines marked `TUNE`) and read after
   `docker compose restart grafana`. Alerts fire into the Grafana UI only until
   a contact point is added under Alerting -> Contact points.

On the application machine, run `./start.sh`, enable the journal, pick `otlp`
and enter `http://<storage machine>:3100/otlp` as the receiver URL; leave the
`Authorization` header empty, this Loki needs none. The script writes to `.env`:

```
LOGS_ENABLE=yes
LOGS_BACKEND=otlp
LOGS_OTLP_EXPORT_ENDPOINT=http://<storage machine>:3100/otlp
LOGS_OTLP_EXPORT_AUTH=
```

With `docker compose` by hand, write these lines yourself and add `logs-otlp`
to `COMPOSE_PROFILES`.

A developer can run this stack on the application machine: with the default
`LOKI_BIND=127.0.0.1` the collector reaches it at
`LOGS_OTLP_EXPORT_ENDPOINT=http://host.docker.internal:3100/otlp` (on Linux add
`extra_hosts: ["host.docker.internal:host-gateway"]` to the collector).

## Elasticsearch + Kibana

On the storage machine, in `logging/elasticsearch`:

1. Create the settings file and keep it `600` (it is in `.gitignore`, together
   with `certs/`):

   ```
   cp elasticsearch.env.example .env
   ```

2. Fill in the required values: `ES_ELASTIC_PASSWORD` (superuser),
   `KIBANA_SYSTEM_PASSWORD`, `KIBANA_ENCRYPTION_KEY` (32+ characters, for
   example `openssl rand -hex 32`; changing it later makes Kibana alert rules
   and connectors unreadable) and `ES_READER_PASSWORD` for the read-only
   account people use in Kibana (empty skips that account).
3. Set `ES_CERT_DNS` / `ES_CERT_IP` to the names and addresses the application
   machine will use in `LOGS_ELASTICSEARCH_URL`: the collector refuses a
   certificate that is not issued for the host it dialled.
4. Review the rest of `.env`: memory (`ES_MEM_LIMIT`, `ES_HEAP_SIZE` = half of
   it), `ES_INDEX_REPLICAS=0` on a single-node cluster, retention
   (`ES_RETENTION`, `ES_ROLLOVER_AGE`, `ES_ROLLOVER_SIZE`), snapshots
   (`ES_SNAPSHOT_SCHEDULE`, `ES_SNAPSHOT_RETENTION`). Snapshots go to a named
   volume by default; move `/snapshots` to a disk of its own with a second
   compose file named in `ES_COMPOSE_OVERRIDE` (then pass both files to
   `docker compose -f docker-compose.yml -f <override>`).
5. Issue the private CA and the certificates of the node and of Kibana into
   `./certs`:

   ```
   ./scripts/make-certs.sh
   ```

   `--nodes` renews the node and Kibana certificates, `--force` issues a new
   CA as well (every client then needs the new `ca.crt`).
6. Start the stack:

   ```
   docker compose up -d
   ```

7. Configure the cluster: `kibana_system` password, writer and reader roles,
   the reader account, lifecycle policy, index template, data stream, snapshot
   repository and schedule, and the API key of the collector. The script is
   idempotent and prints the `LOGS_ELASTICSEARCH_API_KEY=...` line when it
   issues a key:

   ```
   ./scripts/bootstrap.sh
   ```

8. Port 9200 is open on all interfaces by default (TLS only, no anonymous
   access): restrict it with a firewall rule to the application machine.
   Kibana listens on `127.0.0.1:5601`; reach it over an SSH tunnel
   (`ssh -L 5601:127.0.0.1:5601 user@storage-host`) or a reverse proxy, and
   import `certs/ca/ca.crt` into the browser machine once.

On the application machine:

1. Copy `logging/elasticsearch/certs/ca/ca.crt` from the storage machine to
   `otel-collector/es-ca.crt` (that directory is already mounted into the
   collector).
2. Run `./start.sh`, enable the journal, pick `elasticsearch`, enter
   `https://<a name from ES_CERT_DNS>:9200` and either the API key printed by
   `bootstrap.sh` or `rotate-api-key.sh`, or a login and password for a store
   without API keys. The script writes `LOGS_ENABLE`, `LOGS_BACKEND`,
   `LOGS_ELASTICSEARCH_URL` and the chosen credentials to `.env` and clears the
   other pair. `LOGS_ELASTICSEARCH_CA_FILE` defaults to `/etc/otel/es-ca.crt`,
   and `LOGS_ELASTICSEARCH_INDEX` must match `ES_DATA_STREAM` of the storage
   machine (both default to `logs-pneumatic.events.otel-default`).

   On every start in this mode the script creates `./otel-queue`, the
   collector disk queue, and hands it to uid 10001, the user of the collector
   image. With `docker compose` by hand, write the variables yourself, add
   `logs-elasticsearch` to `COMPOSE_PROFILES` and prepare the directory once:

   ```
   mkdir -p otel-queue
   docker run --rm -v "$PWD/otel-queue:/q" alpine chown 10001:10001 /q
   ```

   After the start the collector log has no "permission denied", and
   `ls -l otel-queue/queue` shows the queue database.

The collector API key expires after `ES_API_KEY_EXPIRATION` (90 days). Rotate
it before that: `./scripts/rotate-api-key.sh` on the storage machine, the new
`LOGS_ELASTICSEARCH_API_KEY` into `.env` of the application machine and
`docker compose up -d otel-collector` there, then
`./scripts/rotate-api-key.sh --revoke-old` once events keep arriving.

Stop the collector before restarting Elasticsearch. A store that cannot be
reached at all (connection refused, name does not resolve) makes the exporter
drop the batch instead of retrying it, and by then the records are already out
of the buffer. Watch the counters the collector publishes on `:8888`:

```
docker exec pneumatic-otel-collector wget -qO- localhost:8888/metrics \
  | grep -E 'send_failed_log_records|queue_size'
```

`send_failed_log_records` counts events lost for good, `queue_size` shows how
full the disk queue is; `otel-collector/backend-elasticsearch.yaml` has the
details.

## Further reading

- `otel-collector/base.yaml`, `backend-otlp.yaml`, `backend-elasticsearch.yaml`:
  the collector configuration of each mode.
- The headers of `grafana/docker-compose.yml`, `grafana/grafana.env.example`,
  `elasticsearch/docker-compose.yml`, `elasticsearch/elasticsearch.env.example`
  and `elasticsearch/scripts/*.sh`: details of each setting and step.
