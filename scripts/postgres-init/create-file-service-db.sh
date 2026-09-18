#!/bin/sh

# =============================================================================
# Provision the file service database next to the backend database
#
# The file service keeps its data in its own database and under its own role,
# inside the shared "pneumatic-postgres" container. This script creates both if
# they are missing and does nothing if they already exist.
#
# It runs automatically from /docker-entrypoint-initdb.d when the PostgreSQL
# data directory is initialised. On an installation whose data directory
# already exists it can be executed by hand at any time:
#
#   docker exec pneumatic-postgres sh /docker-entrypoint-initdb.d/create-file-service-db.sh
#
# (scripts/migrate_file_db.sh does exactly that when upgrading.)
# =============================================================================

set -e

FILE_POSTGRES_USER="${FILE_POSTGRES_USER:-pneumatic}"
FILE_POSTGRES_PASSWORD="${FILE_POSTGRES_PASSWORD:-pneumatic}"
FILE_POSTGRES_DB="${FILE_POSTGRES_DB:-pneumatic}"

# Connects over the local socket, where the image trusts every user, so this
# works both during initialisation and inside an already running container.
psql -v ON_ERROR_STOP=1 --no-password \
  --username "${POSTGRES_USER:-postgres}" \
  --dbname postgres \
  -v file_user="$FILE_POSTGRES_USER" \
  -v file_password="$FILE_POSTGRES_PASSWORD" \
  -v file_db="$FILE_POSTGRES_DB" <<'SQL'
SELECT format('CREATE ROLE %I LOGIN PASSWORD %L', :'file_user', :'file_password')
  WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = :'file_user') \gexec
SELECT format('CREATE DATABASE %I OWNER %I', :'file_db', :'file_user')
  WHERE NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = :'file_db') \gexec
-- Only the owner and superusers reach the file service data, the way they did
-- when it lived in a container of its own. Restricted to a database the file
-- service role owns, so that pointing FILE_POSTGRES_DB at an existing database,
-- the backend one included, cannot take privileges away from it.
SELECT format('REVOKE CONNECT ON DATABASE %I FROM PUBLIC', :'file_db')
  FROM pg_database
 WHERE datname = :'file_db' AND pg_get_userbyid(datdba) = :'file_user' \gexec
SQL

echo "File service database \"$FILE_POSTGRES_DB\" is ready"
