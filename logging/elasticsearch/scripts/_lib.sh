#!/bin/bash
# Shared helpers for the logging/elasticsearch scripts. Sourced, not executed.

set -euo pipefail

DEPLOY_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${ENV_FILE:-$DEPLOY_DIR/.env}"

log()  { printf '[INFO] %s\n' "$*"; }
warn() { printf '[WARN] %s\n' "$*" >&2; }
die()  { printf '[FAIL] %s\n' "$*" >&2; exit 1; }

load_env() {
    [ -f "$ENV_FILE" ] || die "no $ENV_FILE - copy elasticsearch.env.example and fill it in"
    set -a
    # shellcheck disable=SC1090
    . "$ENV_FILE"
    set +a
    : "${ES_ELASTIC_PASSWORD:?ES_ELASTIC_PASSWORD is empty in $ENV_FILE}"
}

# ES_COMPOSE_OVERRIDE points at a second compose file for site specific
# changes (another snapshot volume, another port, a second node). Empty by
# default; the scripts and `docker compose` then see exactly the same stack.
compose() {
    if [ -n "${ES_COMPOSE_OVERRIDE:-}" ]; then
        docker compose -f "$DEPLOY_DIR/docker-compose.yml" \
            -f "$ES_COMPOSE_OVERRIDE" --env-file "$ENV_FILE" "$@"
    else
        docker compose -f "$DEPLOY_DIR/docker-compose.yml" \
            --env-file "$ENV_FILE" "$@"
    fi
}

# The curl command every request runs, as a string for `sh -c` inside the
# node container: the certificate authority and the password are already
# there, so neither ever appears in a host process list and the storage
# machine needs no curl of its own. WITH_BODY is "body" when the request
# sends one, and it always arrives through stdin for the same reason.
_es_curl() {
    local method="$1" path="$2" with_body="${3:-none}"
    local cmd='curl -sS --cacert config/certs/ca/ca.crt -u "elastic:$ELASTIC_PASSWORD"'
    cmd="$cmd -X $method -H 'Content-Type: application/json' \"https://localhost:9200$path\""
    if [ "$with_body" = body ]; then
        cmd="$cmd --data-binary @-"
    fi
    printf '%s' "$cmd"
}

# es_api METHOD PATH [BODY_FILE]
es_api() {
    local method="$1" path="$2" body_file="${3:-}"
    if [ -n "$body_file" ]; then
        compose exec -T elasticsearch             sh -c "$(_es_curl "$method" "$path" body)" < "$body_file"
    else
        compose exec -T elasticsearch             sh -c "$(_es_curl "$method" "$path")" < /dev/null
    fi
}

# Same, with the body coming from stdin.
es_api_stdin() {
    compose exec -T elasticsearch sh -c "$(_es_curl "$1" "$2" body)"
}

# json_escape STRING - makes a value safe between the quotes of a JSON string:
# backslash and double quote are escaped. Passwords come from .env and may
# contain either; interpolated raw they break the document or end it early.
json_escape() {
    printf '%s' "$1" | sed -e 's/\\/\\\\/g' -e 's/"/\\"/g'
}

# sed_escape STRING - makes a value safe on the right hand side of the
# `s|...|...|` commands in render(): backslash, the `&` back-reference and the
# `|` delimiter are escaped.
sed_escape() {
    printf '%s' "$1" | sed -e 's/[\\&|]/\\&/g'
}

# Substitutes __PLACEHOLDER__ tokens in a provision file and prints the result.
render() {
    local file="$1"
    sed \
        -e "s|__SHARDS__|$(sed_escape "${ES_INDEX_SHARDS:-1}")|g" \
        -e "s|__REPLICAS__|$(sed_escape "${ES_INDEX_REPLICAS:-1}")|g" \
        -e "s|__INDEX_MODE__|$(sed_escape "${ES_INDEX_MODE:-logsdb}")|g" \
        -e "s|__RETENTION__|$(sed_escape "${ES_RETENTION:-365d}")|g" \
        -e "s|__ROLLOVER_AGE__|$(sed_escape "${ES_ROLLOVER_AGE:-30d}")|g" \
        -e "s|__ROLLOVER_SIZE__|$(sed_escape "${ES_ROLLOVER_SIZE:-50gb}")|g" \
        -e "s|__DATA_STREAM__|$(sed_escape "${ES_DATA_STREAM:-logs-pneumatic.events.otel-default}")|g" \
        -e "s|__INDEX_PATTERN__|$(sed_escape "${ES_INDEX_PATTERN:-logs-pneumatic.events.otel-*}")|g" \
        -e "s|__SNAPSHOT_RETENTION__|$(sed_escape "${ES_SNAPSHOT_RETENTION:-90d}")|g" \
        -e "s|__SNAPSHOT_SCHEDULE__|$(sed_escape "${ES_SNAPSHOT_SCHEDULE:-0 30 1 * * ?}")|g" \
        "$file"
}

require_ok() {
    local response="$1" what="$2"
    case "$response" in
        *'"acknowledged":true'*|*'"acknowledged": true'*) log "$what: ok" ;;
        *'"error"'*) die "$what failed: $response" ;;
        *) log "$what: $response" ;;
    esac
}
