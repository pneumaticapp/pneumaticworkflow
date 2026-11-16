FROM postgres:15-bookworm

# Keep the database bootstrap in scripts/postgres-init so Docker Compose and
# Railway provision the same isolated file-service role and database.
COPY --chmod=755 scripts/postgres-init/create-file-service-db.sh /docker-entrypoint-initdb.d/10-create-file-service-db.sh
