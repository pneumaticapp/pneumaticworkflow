#!/bin/bash
# Brings a freshly started cluster into the state the audit journal needs:
# roles, accounts, index lifecycle, data stream, snapshot repository and
# schedule. Safe to run again - every step is idempotent.
#
#   ./scripts/bootstrap.sh
#
# The API key of the collector is created only if there is no active one with
# the same name. Rotate it with ./scripts/rotate-api-key.sh.

source "$(dirname "${BASH_SOURCE[0]}")/_lib.sh"
load_env

log "waiting for the node to answer"
for _ in $(seq 1 60); do
    health=$(es_api GET '/_cluster/health' 2>/dev/null || true)
    case "$health" in *'"status"'*) break ;; esac
    sleep 5
done
case "${health:-}" in
    *'"status"'*) log "cluster: $health" ;;
    *) die "the node is not answering, look at: docker compose logs elasticsearch" ;;
esac

log "--- 1. Kibana account ---"
printf '{"password":"%s"}' "$(json_escape "$KIBANA_SYSTEM_PASSWORD")" \
    | es_api_stdin POST '/_security/user/kibana_system/_password' > /dev/null
log "kibana_system password set"

log "--- 2. Roles ---"
require_ok "$(render "$PROVISION/role-collector-writer.json" \
    | es_api_stdin PUT '/_security/role/pneumatic_events_writer')" \
    "role pneumatic_events_writer"
require_ok "$(render "$PROVISION/role-kibana-reader.json" \
    | es_api_stdin PUT '/_security/role/pneumatic_events_reader')" \
    "role pneumatic_events_reader"

if [ -n "${ES_READER_PASSWORD:-}" ]; then
    printf '{"password":"%s","roles":["pneumatic_events_reader"],"full_name":"Pneumatic audit journal reader"}' \
        "$(json_escape "$ES_READER_PASSWORD")" \
        | es_api_stdin PUT "/_security/user/${ES_READER_USER:-pneumatic-reader}" > /dev/null
    log "user ${ES_READER_USER:-pneumatic-reader}: ok"
else
    warn "ES_READER_PASSWORD is empty, the read only account was not created"
fi

log "--- 3. Index lifecycle ---"
require_ok "$(render "$PROVISION/ilm-policy.json" \
    | es_api_stdin PUT "/_ilm/policy/$ILM_POLICY")" "policy $ILM_POLICY"

log "--- 4. Index template ---"
# logs-otel@custom is the extension point of the built-in logs-otel@template:
# that template already lists it in composed_of, so Elasticsearch keeps
# handling the OTel document shape and only the settings below are ours.
require_ok "$(render "$PROVISION/component-template-logs-otel-custom.json" \
    | es_api_stdin PUT '/_component_template/logs-otel@custom')" \
    "component template logs-otel@custom"

log "--- 5. Data stream ---"
if es_api GET "/_data_stream/$ES_DATA_STREAM" | grep -q '"name"'; then
    log "data stream $ES_DATA_STREAM already exists"
    write_index=$(es_api GET "/_data_stream/$ES_DATA_STREAM?filter_path=data_streams.indices.index_name" \
        | tr ',' '\n' | sed -n 's/.*"index_name":"\([^"]*\)".*/\1/p' | tail -1)
    # Read the effective policy before changing anything: the PUT below would
    # make every index look right and hide the fact that the write index still
    # carries the settings of the old template.
    write_index_policy=$(es_api GET "/$write_index/_ilm/explain?filter_path=indices.*.policy")

    # Indices created before this template keep the policy they were born
    # with - by default the built-in `logs` one, which has no delete phase at
    # all. Left alone they would be kept forever.
    printf '{"index.lifecycle.name":"%s"}' "$ILM_POLICY" \
        | es_api_stdin PUT "/$ES_DATA_STREAM/_settings" > /dev/null
    log "every backing index now follows $ILM_POLICY"

    case "$write_index_policy" in
        *"$ILM_POLICY"*)
            log "the write index was already on the policy, no rollover" ;;
        *)
            # Settings of a template apply to indices created after it, so the
            # rollover is what turns the change into a new backing index.
            es_api POST "/$ES_DATA_STREAM/_rollover" > /dev/null
            log "rolled over, the new write index carries the new settings"
            ;;
    esac
else
    es_api PUT "/_data_stream/$ES_DATA_STREAM" > /dev/null
    log "data stream $ES_DATA_STREAM created"
fi

log "--- 6. Snapshots ---"
es_container=$(compose ps -q elasticsearch)
[ -n "$es_container" ] || die "the elasticsearch container is not running"
# A fresh named volume belongs to root and the node runs as uid 1000, so the
# repository directory has to be handed over once. Done from a throwaway
# container of the same image - no second image to pull.
MSYS_NO_PATHCONV=1 docker run --rm --volumes-from "$es_container" -u 0 \
    --entrypoint sh "$ES_IMAGE" \
    -c 'mkdir -p /snapshots && chown 1000:0 /snapshots && chmod 770 /snapshots'

require_ok "$(render "$PROVISION/snapshot-repository.json" \
    | es_api_stdin PUT "/_snapshot/$SNAPSHOT_REPOSITORY")" "repository $SNAPSHOT_REPOSITORY"
verify=$(es_api POST "/_snapshot/$SNAPSHOT_REPOSITORY/_verify")
case "$verify" in
    *'"nodes"'*) log "repository is writable from every node" ;;
    *) die "the repository is not writable: $verify" ;;
esac
require_ok "$(render "$PROVISION/slm-policy.json" \
    | es_api_stdin PUT "/_slm/policy/$SLM_POLICY")" "schedule $SLM_POLICY"

log "--- 7. API key of the collector ---"
existing=$(es_api GET "/_security/api_key?name=$API_KEY_NAME&active_only=true")
case "$existing" in
    *'"api_keys":[]'*|*'"api_keys" : [ ]'*)
        "$DEPLOY_DIR/scripts/rotate-api-key.sh"
        ;;
    *)
        log "an active key named $API_KEY_NAME already exists, keeping it"
        log "rotate it with ./scripts/rotate-api-key.sh"
        ;;
esac

log "--- done ---"
es_api GET '/_cluster/health?pretty'
