#!/bin/bash
# Issues a new API key for the collector and prints the line to put into the
# .env of the application machine. The old keys stay valid until you invalidate
# them, so the swap has no gap:
#
#   1. ./scripts/rotate-api-key.sh              on the storage machine
#   2. LOGS_ELASTICSEARCH_API_KEY=...           into .env of the application
#      docker compose up -d otel-collector      restart, events keep flowing
#   3. ./scripts/rotate-api-key.sh --revoke-old once the new key is confirmed
#
# SOC DAT-05 asks for a written rotation procedure; this is it. Do it every 90
# days - that is also the lifetime of the key itself, so a forgotten rotation
# stops the delivery instead of leaving a valid key lying around forever.

source "$(dirname "${BASH_SOURCE[0]}")/_lib.sh"
load_env

API_KEY_NAME="pneumatic-collector"
EXPIRATION="${ES_API_KEY_EXPIRATION:-90d}"
PROVISION="$DEPLOY_DIR/provision"

if [ "${1:-}" = "--revoke-old" ]; then
    log "invalidating every key named $API_KEY_NAME except the newest one"
    # `|| true`: with no active key grep finds nothing and exits 1, which
    # under pipefail would end the script here without a word.
    keys=$(es_api GET "/_security/api_key?name=$API_KEY_NAME&active_only=true" \
        | tr ',' '\n' | grep '"id"' | sed 's/.*"id":"\([^"]*\)".*/\1/' || true)
    if [ -z "$keys" ]; then
        log "no active key named $API_KEY_NAME, nothing to invalidate"
        log "issue one first: ./scripts/rotate-api-key.sh"
        exit 0
    fi
    newest=$(printf '%s\n' "$keys" | tail -1)
    for id in $keys; do
        [ "$id" = "$newest" ] && continue
        printf '{"ids":["%s"]}' "$id" \
            | es_api_stdin DELETE '/_security/api_key' > /dev/null
        log "invalidated $id"
    done
    log "active keys now:"
    es_api GET "/_security/api_key?name=$API_KEY_NAME&active_only=true&filter_path=api_keys.id,api_keys.creation,api_keys.expiration"
    exit 0
fi

# The key carries the writer role inline, so it can append to the journal and
# do nothing else even if the role on the cluster is changed later.
descriptor=$(render "$PROVISION/role-collector-writer.json")
response=$(printf '{"name":"%s","expiration":"%s","role_descriptors":{"pneumatic_events_writer":%s}}' \
    "$API_KEY_NAME" "$(json_escape "$EXPIRATION")" "$descriptor" \
    | es_api_stdin POST '/_security/api_key')

encoded=$(printf '%s' "$response" | sed -n 's/.*"encoded":"\([^"]*\)".*/\1/p')
[ -n "$encoded" ] || die "no key in the answer: $response"

cat <<EOF

New API key, valid for $EXPIRATION. It is shown once and stored nowhere.

Put these lines into the .env of the APPLICATION machine and restart the
collector (docker compose up -d otel-collector):

LOGS_ELASTICSEARCH_API_KEY=$encoded

Then check that events keep arriving:
  curl --cacert ca.crt -u <reader> "https://<store>:9200/${ES_DATA_STREAM:-logs-pneumatic.events.otel-default}/_count"
and only then run:
  ./scripts/rotate-api-key.sh --revoke-old
EOF
