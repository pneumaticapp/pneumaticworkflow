#!/bin/bash
# Issues the private CA and the TLS certificates of the node and of Kibana.
#
#   ./scripts/make-certs.sh              # creates what is missing, keeps the rest
#   ./scripts/make-certs.sh --nodes      # renews node and Kibana, keeps the CA
#   ./scripts/make-certs.sh --force      # new CA as well (every client must
#                                        # get the new ca.crt afterwards)
#
# Names go into the certificate from ES_CERT_DNS and ES_CERT_IP: the collector
# verifies the host name it dialled against them, so the address written in
# LOGS_ELASTICSEARCH_URL on the application machine has to be in that list.

source "$(dirname "${BASH_SOURCE[0]}")/_lib.sh"
load_env

CERT_DIR="$DEPLOY_DIR/certs"
IMAGE="${ES_IMAGE:-docker.elastic.co/elasticsearch/elasticsearch:9.5.3}"
CA_DAYS="${ES_CA_DAYS:-3650}"
CERT_DAYS="${ES_CERT_DAYS:-730}"
MODE="${1:-}"

mkdir -p "$CERT_DIR"

if [ "$MODE" = "--force" ]; then
    log "removing the old CA and every certificate signed by it"
    rm -rf "$CERT_DIR/ca" "$CERT_DIR/es" "$CERT_DIR/kibana"
elif [ "$MODE" = "--nodes" ]; then
    [ -f "$CERT_DIR/ca/ca.key" ] || die "no CA in $CERT_DIR/ca - run without arguments first"
    rm -rf "$CERT_DIR/es" "$CERT_DIR/kibana"
elif [ -f "$CERT_DIR/es/es.crt" ]; then
    log "certificates already exist, nothing to do (--nodes renews, --force starts over)"
    exit 0
fi

# The instance list is generated, not stored: it is a projection of .env and a
# stale copy would issue a certificate for the wrong host name.
cat > "$CERT_DIR/instances.yml" <<EOF
instances:
  - name: es
    dns:
      - elasticsearch
      - pneumatic-elasticsearch
      - localhost
$(for n in ${ES_CERT_DNS:-}; do echo "      - $n"; done)
    ip:
      - 127.0.0.1
$(for a in ${ES_CERT_IP:-}; do echo "      - $a"; done)
  - name: kibana
    dns:
      - kibana
      - pneumatic-kibana
      - localhost
$(for n in ${KIBANA_CERT_DNS:-}; do echo "      - $n"; done)
    ip:
      - 127.0.0.1
$(for a in ${KIBANA_CERT_IP:-}; do echo "      - $a"; done)
EOF

log "issuing certificates (CA $CA_DAYS days, nodes $CERT_DAYS days)"
MSYS_NO_PATHCONV=1 docker run --rm \
    -v "$CERT_DIR:/certs" \
    -w /usr/share/elasticsearch \
    "$IMAGE" bash -c "
        set -e
        if [ ! -f /certs/ca/ca.crt ]; then
            bin/elasticsearch-certutil ca --silent --pem --days $CA_DAYS --out /certs/ca.zip
            unzip -q -o /certs/ca.zip -d /certs
            rm -f /certs/ca.zip
        fi
        bin/elasticsearch-certutil cert --silent --pem --days $CERT_DAYS \
            --in /certs/instances.yml --out /certs/certs.zip \
            --ca-cert /certs/ca/ca.crt --ca-key /certs/ca/ca.key
        unzip -q -o /certs/certs.zip -d /certs
        rm -f /certs/certs.zip
        chmod 644 /certs/ca/ca.crt /certs/es/es.crt /certs/kibana/kibana.crt
        chmod 640 /certs/ca/ca.key /certs/es/es.key /certs/kibana/kibana.key
    "

log "expiry dates:"
# keytool, not openssl: the Elasticsearch image ships a JDK and no openssl.
MSYS_NO_PATHCONV=1 docker run --rm -v "$CERT_DIR:/certs" --entrypoint sh "$IMAGE" -c '
    for c in /certs/ca/ca.crt /certs/es/es.crt /certs/kibana/kibana.crt; do
        printf "  %s  " "$c"
        /usr/share/elasticsearch/jdk/bin/keytool -printcert -file "$c" \
            | grep -m1 "Valid from"
    done'

cat <<EOF

Done. Files are in $CERT_DIR:
  ca/ca.crt        give this one to the collector (logging/otel/es-ca.crt on
                   the application machine) and to every browser that opens
                   Kibana
  ca/ca.key        never leaves this machine, back it up separately
  es/, kibana/     node and Kibana certificates

After a renewal restart the containers:  docker compose restart
EOF
