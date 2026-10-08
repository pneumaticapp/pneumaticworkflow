# Pneumatic audit journal storage

The storage side of the Pneumatic audit journal: the services that keep the
user action events and let people search and chart them.

The application machine does not run anything from this directory. There the
backend and the file service write events into a Redis stream, and the
OpenTelemetry collector (`otel-collector/` in the root of the repository)
forwards them to the store named by `LOGS_BACKEND` in `.env`. `start.sh` starts
the collector on its own when `LOGS_BACKEND` is `otlp` or `elasticsearch`
(compose profiles `logs-otlp` / `logs-elasticsearch`); with `LOGS_BACKEND`
unset, the default, the journal is off and no collector runs.

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

On the application machine, in `.env`:

```
LOGS_BACKEND=otlp
LOGS_OTLP_EXPORT_ENDPOINT=http://<storage machine>:3100/otlp
```

`LOGS_OTLP_EXPORT_AUTH` is the whole `Authorization` header value for a
receiver that needs one; this Loki does not. Then run `./start.sh` (it adds the
`logs-otlp` profile), or with `docker compose` by hand set
`COMPOSE_PROFILES=logs-otlp` in `.env`.

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
2. Hand the queue volume to the collector once, before the first start:

   ```
   docker volume create pneumatic_otel-queue
   docker run --rm -v pneumatic_otel-queue:/q alpine chown 10001:10001 /q
   ```

3. In `.env`:

   ```
   LOGS_BACKEND=elasticsearch
   LOGS_ELASTICSEARCH_URL=https://<a name from ES_CERT_DNS>:9200
   LOGS_ELASTICSEARCH_API_KEY=<printed by bootstrap.sh or rotate-api-key.sh>
   ```

   `LOGS_ELASTICSEARCH_CA_FILE` defaults to `/etc/otel/es-ca.crt`, and
   `LOGS_ELASTICSEARCH_INDEX` must match `ES_DATA_STREAM` of the storage
   machine (both default to `logs-pneumatic.events.otel-default`).
   `LOGS_ELASTICSEARCH_USER` / `LOGS_ELASTICSEARCH_PASSWORD` replace the API key
   for a store without API keys; set one or the other, never both.
4. Run `./start.sh` (it adds the `logs-elasticsearch` profile), or with
   `docker compose` by hand set `COMPOSE_PROFILES=logs-elasticsearch` in
   `.env`.

The collector API key expires after `ES_API_KEY_EXPIRATION` (90 days). Rotate
it before that: `./scripts/rotate-api-key.sh` on the storage machine, the new
`LOGS_ELASTICSEARCH_API_KEY` into `.env` of the application machine and
`docker compose up -d otel-collector` there, then
`./scripts/rotate-api-key.sh --revoke-old` once events keep arriving.

Stop the collector before restarting Elasticsearch: batches sent to a store
that cannot be reached at all are dropped, not retried (see the Elasticsearch
section of `default.env`).

## Further reading

- `default.env`, section "Logging / Events": every variable of the application
  machine.
- `otel-collector/base.yaml`, `backend-otlp.yaml`, `backend-elasticsearch.yaml`:
  the collector configuration of each mode.
- The headers of `grafana/docker-compose.yml`, `grafana/grafana.env.example`,
  `elasticsearch/docker-compose.yml`, `elasticsearch/elasticsearch.env.example`
  and `elasticsearch/scripts/*.sh`: details of each setting and step.
