#!/bin/sh
# Run in an ephemeral nginx:alpine container with the repo mounted at /workspace.
set -eu
mkdir -p /etc/nginx/includes /tmp/gunicorn
cp /workspace/nginx/includes/* /etc/nginx/includes/
export SERVER_ADDRESS=localhost
envsubst '${SERVER_ADDRESS}' < /workspace/nginx/templates/nginx.conf.template > /etc/nginx/nginx.conf
nginx -t

export PORT=8080 NAMESERVER=127.0.0.11 FRONTEND_HOST=127.0.0.1:8000
export BACKEND_HOST=127.0.0.1:8001 FILE_SERVICE_HOST=127.0.0.1:8002 MCP_HOST=127.0.0.1:8003
envsubst '${PORT} ${NAMESERVER} ${FRONTEND_HOST} ${BACKEND_HOST} ${FILE_SERVICE_HOST} ${MCP_HOST}' < /workspace/nginx/railway/nginx.conf > /etc/nginx/nginx.conf
nginx -t
