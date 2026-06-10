#!/bin/sh
set -e

# Extract nameserver from /etc/resolv.conf for nginx resolver directive
# Railway uses internal DNS that changes on redeploy
NAMESERVER=$(grep nameserver /etc/resolv.conf | head -1 | awk '{print $2}')
if [ -z "$NAMESERVER" ]; then
  echo "ERROR: no nameserver found in /etc/resolv.conf" >&2
  exit 1
fi
export NAMESERVER

# Default PORT if not set
export PORT=${PORT:-8080}

# Substitute environment variables in nginx.conf
envsubst '${PORT} ${NAMESERVER} ${FRONTEND_HOST} ${BACKEND_HOST} ${FILE_SERVICE_HOST}' \
  < /etc/nginx/nginx.conf \
  > /etc/nginx/nginx.conf.tmp

mv /etc/nginx/nginx.conf.tmp /etc/nginx/nginx.conf

echo "Starting nginx with resolver=$NAMESERVER on port=$PORT"
echo "  FRONTEND_HOST=$FRONTEND_HOST"
echo "  BACKEND_HOST=$BACKEND_HOST"
echo "  FILE_SERVICE_HOST=$FILE_SERVICE_HOST"

exec "$@"
