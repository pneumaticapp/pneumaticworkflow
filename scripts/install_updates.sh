#!/usr/bin/env bash
set -euo pipefail

echo "==> Pulling latest code..."
git pull origin master

echo "==> Building new images..."
docker compose build backend celery celery-beat frontend

echo "==> Restarting containers..."
docker compose up -d --no-deps --force-recreate celery celery-beat backend frontend

echo "==> Reloading nginx..."
docker compose exec nginx nginx -s reload

echo "==> Pruning dangling images..."
docker image prune -f

echo "==> Deployment complete."
