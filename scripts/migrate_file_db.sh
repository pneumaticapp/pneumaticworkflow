#!/bin/bash

# =============================================================================
# Move the file service database into the shared "pneumatic-postgres" container
#
# Earlier versions ran the file service database in a separate container
# ("pneumatic-file-postgres", data in "file-postgres/data"). It now lives in
# "pneumatic-postgres" as a separate database, provisioned by
# "scripts/postgres-init/create-file-service-db.sh" when that container
# initialises its data directory. An installation that is being upgraded already
# has an initialised data directory, so run this script once. It:
#   1. dumps the legacy database into "postgres/backups" (if there is one)
#   2. creates the file service role and database in "pneumatic-postgres"
#   3. restores the dump there (the target database is overwritten)
#   4. removes the legacy container and starts the stack
# The legacy data directory "file-postgres/data" is left untouched.
#
# Upgrading from a version without a file service works too: there is nothing
# to copy, so the script only creates the database.
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
BACKUPS_DIR="$PROJECT_DIR/postgres/backups"
LEGACY_DATA_DIR="$PROJECT_DIR/file-postgres/data"

LEGACY_CONTAINER="pneumatic-file-postgres"
TEMP_CONTAINER="pneumatic-file-postgres-migration"
TARGET_CONTAINER="pneumatic-postgres"
FILE_SERVICE_CONTAINER="pneumatic-file-service"
NGINX_CONTAINER="pneumatic-nginx"
POSTGRES_IMAGE="postgres:15-bookworm"
INIT_SCRIPT="/docker-entrypoint-initdb.d/create-file-service-db.sh"

# =============================================================================
# Color output helpers
# =============================================================================

RED='\033[0;31m'
ORANGE='\033[0;33m'
GREEN='\033[0;32m'
NC='\033[0m'

print_error()   { echo -e "${RED}$1${NC}"; }
print_warning() { echo -e "${ORANGE}$1${NC}"; }
print_info()    { echo -e "${GREEN}$1${NC}"; }

TEMP_CONTAINER_CREATED=false
FILE_SERVICE_STOPPED=false
LEGACY_STOPPED=false

fail() {
  print_error "$1"
  if [ "$TEMP_CONTAINER_CREATED" = true ]; then
    docker rm -f "$TEMP_CONTAINER" > /dev/null 2>&1
  fi
  if [ "$FILE_SERVICE_STOPPED" = true ]; then
    # Deliberately not restarted: the database may be half copied, and serving
    # files from it would be worse than serving none.
    print_warning "Container \"$FILE_SERVICE_CONTAINER\" is still stopped. Fix the problem and run this script again, or start it with: docker start $FILE_SERVICE_CONTAINER"
  fi
  if [ "$LEGACY_STOPPED" = true ]; then
    print_warning "Legacy container \"$LEGACY_CONTAINER\" is stopped but still holds the original data."
  fi
  exit 1
}

# Cancelling is only offered while nothing has been overwritten yet, so put the
# stack back the way it was found rather than leaving the file service down.
cancel() {
  print_warning "Operation cancelled."
  if [ "$TEMP_CONTAINER_CREATED" = true ]; then
    docker rm -f "$TEMP_CONTAINER" > /dev/null 2>&1
  fi
  if [ "$LEGACY_STOPPED" = true ]; then
    if docker start "$LEGACY_CONTAINER" > /dev/null 2>&1; then
      print_info "Legacy container \"$LEGACY_CONTAINER\" started again"
    else
      print_warning "Could not start \"$LEGACY_CONTAINER\" again. Start it with: docker start $LEGACY_CONTAINER"
    fi
  fi
  if [ "$FILE_SERVICE_STOPPED" = true ]; then
    if docker start "$FILE_SERVICE_CONTAINER" > /dev/null 2>&1; then
      print_info "Container \"$FILE_SERVICE_CONTAINER\" started again"
    else
      print_warning "Could not start \"$FILE_SERVICE_CONTAINER\" again. Start it with: docker start $FILE_SERVICE_CONTAINER"
    fi
  fi
  exit 0
}

# Row count of every table in the file service database, one "table=count" line
# each. The copy is verified against this rather than against a single table, so
# that a partial restore cannot pass unnoticed. Returns non-zero when the
# database cannot be read at all, which is different from it having no tables.
table_counts() {
  local out
  out=$(docker exec "$1" psql -U "$FILE_POSTGRES_USER" -d "$FILE_POSTGRES_DB" -tAc "
    SELECT tablename || '=' || (xpath('/row/c/text()',
             query_to_xml(format('SELECT count(*) AS c FROM public.%I', tablename), false, true, '')))[1]::text
      FROM pg_tables
     WHERE schemaname = 'public'
     ORDER BY tablename" 2>&1) || { printf '%s\n' "$out" >&2; return 1; }
  printf '%s' "$out" | tr -d '\r' | sed '/^$/d'
}

# Same counts on one line, for reporting.
format_counts() {
  if [ -z "$1" ]; then
    echo "no tables"
  else
    echo "$1" | tr '\n' ' ' | sed 's/[[:space:]]*$//'
  fi
}

confirm() {
  while true; do
    read -r -p "$1 (y/n): " answer || fail "No input received, aborting."
    case "$answer" in
      y) return 0 ;;
      n) cancel ;;
      *) ;;
    esac
  done
}

# =============================================================================
# Section 1: Locate the legacy file service database
# =============================================================================

# 1.1 Without a reachable Docker daemon every check below would report the wrong
# thing, so stop here instead.
if ! docker info > /dev/null 2>&1; then
  fail "Docker is not available. Start Docker and run this script again."
fi

if docker container inspect "$LEGACY_CONTAINER" > /dev/null 2>&1; then
  LEGACY_SOURCE="container"
  print_info "Found legacy container \"$LEGACY_CONTAINER\""
elif [ -f "$LEGACY_DATA_DIR/PG_VERSION" ]; then
  LEGACY_SOURCE="data-dir"
  print_info "Found legacy data directory \"file-postgres/data\" (container \"$LEGACY_CONTAINER\" no longer exists)"
else
  LEGACY_SOURCE="none"
  print_info "No legacy file service database found. The file service database will only be created."
fi
echo ""

# =============================================================================
# Section 2: Select docker-compose configuration
# =============================================================================

print_info "Select the docker-compose configuration you run Pneumatic with:"
echo ""
echo "  1. Root (from sources)"
echo "  2. Root (stable)"
echo "  3. Root (latest)"
echo "  4. Frontend"
echo ""

while true; do
  read -r -p "Enter configuration number (1-4): " COMPOSE_FILE || fail "No input received, aborting."

  if ! [[ "$COMPOSE_FILE" =~ ^[0-9]+$ ]]; then
    print_error "Enter the configuration number"
    continue
  fi

  if [ "$COMPOSE_FILE" -lt 1 ] || [ "$COMPOSE_FILE" -gt 4 ]; then
    print_error "Entered number does not match any configuration from the list"
    continue
  fi

  break
done

COMPOSE_TAG=""
case "$COMPOSE_FILE" in
  1) COMPOSE_LABEL="Root (from sources)"; ENV_FILE="$PROJECT_DIR/.env";          COMPOSE_ARGS=('-f' "$PROJECT_DIR/docker-compose.src.yml") ;;
  2) COMPOSE_LABEL="Root (stable)";       ENV_FILE="$PROJECT_DIR/.env";          COMPOSE_ARGS=('-f' "$PROJECT_DIR/docker-compose.yml"); COMPOSE_TAG="stable" ;;
  3) COMPOSE_LABEL="Root (latest)";       ENV_FILE="$PROJECT_DIR/.env";          COMPOSE_ARGS=('-f' "$PROJECT_DIR/docker-compose.yml"); COMPOSE_TAG="latest" ;;
  4) COMPOSE_LABEL="Frontend";            ENV_FILE="$PROJECT_DIR/frontend/.env"; COMPOSE_ARGS=('-f' "$PROJECT_DIR/frontend/docker-compose.yml") ;;
esac

# Compose resolves .env from the compose file's directory; pass the selected file explicitly.
if [ -f "$ENV_FILE" ]; then
  COMPOSE_ARGS=('--env-file' "$ENV_FILE" "${COMPOSE_ARGS[@]}")
fi

compose() {
  if [ -n "$COMPOSE_TAG" ]; then
    TAG="$COMPOSE_TAG" docker compose "${COMPOSE_ARGS[@]}" "$@"
  else
    docker compose "${COMPOSE_ARGS[@]}" "$@"
  fi
}

echo ""
print_info "Selected configuration: $COMPOSE_LABEL"
echo ""

# =============================================================================
# Section 3: Read .env file and extract database configuration
# =============================================================================

POSTGRES_USER="postgres_user"
POSTGRES_DB="postgres_db"
FILE_POSTGRES_USER="pneumatic"
FILE_POSTGRES_PASSWORD="pneumatic"
FILE_POSTGRES_DB="pneumatic"

if [ -f "$ENV_FILE" ]; then
  while IFS='=' read -r key value || [ -n "$key" ]; do
    key=$(echo "$key" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
    value=$(echo "$value" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')

    [ -z "$key" ] && continue
    [[ "$key" == \#* ]] && continue

    value=$(echo "$value" | sed 's/[[:space:]]\+#.*$//;s/[[:space:]]*$//')
    # docker compose strips surrounding quotes from .env values, so do the same
    value=$(printf '%s' "$value" | sed -e 's/^"\(.*\)"$/\1/' -e "s/^'\(.*\)'\$/\1/")

    case "$key" in
      POSTGRES_USER)          POSTGRES_USER="$value" ;;
      POSTGRES_DB)            POSTGRES_DB="$value" ;;
      FILE_POSTGRES_USER)     FILE_POSTGRES_USER="$value" ;;
      FILE_POSTGRES_PASSWORD) FILE_POSTGRES_PASSWORD="$value" ;;
      FILE_POSTGRES_DB)       FILE_POSTGRES_DB="$value" ;;
    esac
  done < "$ENV_FILE"
else
  print_warning "No .env file found at $ENV_FILE, using default database configuration."
fi

# =============================================================================
# Section 4: Confirm migration
# =============================================================================

# 4.1 The file service database is dropped and recreated below, so it must not
# be the backend database.
if [ "$FILE_POSTGRES_DB" = "$POSTGRES_DB" ]; then
  fail "FILE_POSTGRES_DB and POSTGRES_DB are both \"$FILE_POSTGRES_DB\". This script recreates the file service database, which would destroy the backend database. Give the file service a database of its own in $ENV_FILE."
fi

if [ "$LEGACY_SOURCE" != "none" ]; then
  print_warning "The file service database will be copied into container \"$TARGET_CONTAINER\" (database \"$FILE_POSTGRES_DB\", role \"$FILE_POSTGRES_USER\")."
  print_warning "Any data already in that target database will be overwritten."
  print_warning "The file service will be stopped while the migration runs."
  confirm "Continue?"
  echo ""
fi

# =============================================================================
# Section 5: Stop the file service and dump the legacy database
# =============================================================================

# 5.1 Stop the file service before the legacy database is read. Stopping it
# afterwards would leave a window in which an upload lands in the old database
# and never reaches the new one.
if docker container inspect "$FILE_SERVICE_CONTAINER" > /dev/null 2>&1; then
  output=$(docker stop "$FILE_SERVICE_CONTAINER" 2>&1) || fail "Could not stop \"$FILE_SERVICE_CONTAINER\": $output"
  FILE_SERVICE_STOPPED=true
  print_info "Container \"$FILE_SERVICE_CONTAINER\" stopped"
fi

if [ "$LEGACY_SOURCE" != "none" ]; then

  # 5.2 Make the legacy database reachable
  if [ "$LEGACY_SOURCE" = "container" ]; then
    SOURCE_CONTAINER="$LEGACY_CONTAINER"
    if [ "$(docker container inspect -f '{{.State.Running}}' "$LEGACY_CONTAINER")" != "true" ]; then
      output=$(docker start "$LEGACY_CONTAINER" 2>&1) || fail "$output"
      print_info "Legacy container \"$LEGACY_CONTAINER\" started"
    fi
  else
    # The legacy container is gone: run a temporary PostgreSQL on the old data directory.
    SOURCE_CONTAINER="$TEMP_CONTAINER"
    docker rm -f "$TEMP_CONTAINER" > /dev/null 2>&1
    MOUNT_SRC="$LEGACY_DATA_DIR"
    if command -v cygpath > /dev/null 2>&1; then
      MOUNT_SRC="$(cygpath -w "$LEGACY_DATA_DIR")"
    fi
    output=$(MSYS_NO_PATHCONV=1 docker run -d --name "$TEMP_CONTAINER" \
      -v "$MOUNT_SRC:/var/lib/postgresql/data" \
      -e POSTGRES_PASSWORD="$FILE_POSTGRES_PASSWORD" \
      "$POSTGRES_IMAGE" 2>&1) || fail "$output"
    TEMP_CONTAINER_CREATED=true
    print_info "Temporary container \"$TEMP_CONTAINER\" started on \"file-postgres/data\""
  fi

  # 5.3 Wait for the legacy database to become available
  print_info "Waiting for the legacy database to become available..."
  MAX_RETRIES=30
  RETRY_COUNT=0
  while true; do
    docker exec "$SOURCE_CONTAINER" pg_isready -U "$FILE_POSTGRES_USER" -d "$FILE_POSTGRES_DB" > /dev/null 2>&1
    if [ $? -eq 0 ]; then
      print_info "Legacy database is ready"
      break
    fi

    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ "$RETRY_COUNT" -ge "$MAX_RETRIES" ]; then
      fail "Legacy database is not available after ${MAX_RETRIES} seconds"
    fi

    sleep 1
  done

  SOURCE_COUNTS=$(table_counts "$SOURCE_CONTAINER") || fail "Could not read the tables of the legacy database \"$FILE_POSTGRES_DB\". Nothing has been changed."
  print_info "Legacy database contains: $(format_counts "$SOURCE_COUNTS")"

  # 5.4 Save a plain SQL dump into postgres/backups
  mkdir -p "$BACKUPS_DIR"
  DUMP_FILENAME="pneumatic-file-postgres-$(date +%Y-%m-%d_%H-%M-%S).sql"
  print_info "Dumping legacy database to \"postgres/backups/$DUMP_FILENAME\"..."
  docker exec "$SOURCE_CONTAINER" pg_dump -U "$FILE_POSTGRES_USER" --no-owner --no-privileges "$FILE_POSTGRES_DB" > "$BACKUPS_DIR/$DUMP_FILENAME"
  if [ $? -ne 0 ] || [ ! -s "$BACKUPS_DIR/$DUMP_FILENAME" ]; then
    rm -f "$BACKUPS_DIR/$DUMP_FILENAME"
    fail "Failed to dump the legacy database"
  fi
  print_info "Dump saved"

  # 5.5 The legacy database has been read, so stop its container. It publishes
  # the same host port as the shared database container does in the frontend
  # configuration, and the next step could not bind that port otherwise.
  if [ "$LEGACY_SOURCE" = "container" ]; then
    output=$(docker stop "$LEGACY_CONTAINER" 2>&1) || fail "Could not stop \"$LEGACY_CONTAINER\": $output"
    LEGACY_STOPPED=true
    print_info "Legacy container \"$LEGACY_CONTAINER\" stopped"
  fi
  echo ""

fi

# =============================================================================
# Section 6: Create the file service database in pneumatic-postgres
# =============================================================================

# 6.1 Start the shared database container
output=$(compose up -d postgres 2>&1) || fail "$output"

print_info "Waiting for container \"$TARGET_CONTAINER\" to become available..."
MAX_RETRIES=60
RETRY_COUNT=0
while true; do
  docker exec "$TARGET_CONTAINER" pg_isready -h localhost -U "$POSTGRES_USER" > /dev/null 2>&1
  if [ $? -eq 0 ]; then
    print_info "Container \"$TARGET_CONTAINER\" is ready"
    break
  fi

  RETRY_COUNT=$((RETRY_COUNT + 1))
  if [ "$RETRY_COUNT" -ge "$MAX_RETRIES" ]; then
    fail "Container \"$TARGET_CONTAINER\" is not available after ${MAX_RETRIES} seconds"
  fi

  sleep 1
done

# 6.2 Run the same provisioning script the container runs on a fresh data directory
# MSYS_NO_PATHCONV keeps Git Bash on Windows from rewriting the container path.
output=$(MSYS_NO_PATHCONV=1 docker exec "$TARGET_CONTAINER" sh "$INIT_SCRIPT" 2>&1) || fail "$output"
print_info "Role \"$FILE_POSTGRES_USER\" and database \"$FILE_POSTGRES_DB\" are present in \"$TARGET_CONTAINER\""
echo ""

# =============================================================================
# Section 7: Restore the dump into pneumatic-postgres
# =============================================================================

if [ "$LEGACY_SOURCE" != "none" ]; then

  # 7.1 Guard against overwriting records created after the upgrade
  # alembic_version only records the schema version, it is not data worth keeping.
  # Read separately from the sum: inside a pipeline the exit status would be
  # awk's, so an unreadable database would look empty and skip the warning.
  TARGET_COUNTS=$(table_counts "$TARGET_CONTAINER") || fail "Could not read the target database \"$FILE_POSTGRES_DB\". Nothing has been overwritten."
  TARGET_ROWS=$(printf '%s\n' "$TARGET_COUNTS" | grep -v '^alembic_version=' | awk -F= '{sum += $2} END {print sum + 0}')
  if [ "$TARGET_ROWS" -gt 0 ]; then
    print_warning "WARNING: database \"$FILE_POSTGRES_DB\" in \"$TARGET_CONTAINER\" already contains $TARGET_ROWS record(s)."
    print_warning "They will be replaced by the contents of the legacy database."
    confirm "Overwrite them?"
  fi

  # 7.2 Recreate the target database through the provisioning script, so that it
  # ends up with the same owner and privileges as on a fresh installation
  output=$(docker exec "$TARGET_CONTAINER" dropdb -U "$POSTGRES_USER" --force --if-exists "$FILE_POSTGRES_DB" 2>&1) || fail "$output"
  output=$(MSYS_NO_PATHCONV=1 docker exec "$TARGET_CONTAINER" sh "$INIT_SCRIPT" 2>&1) || fail "$output"
  print_info "Database \"$FILE_POSTGRES_DB\" recreated"

  # 7.3 Restore the dump as the file service role so it owns every object
  print_info "Restoring \"$DUMP_FILENAME\" into \"$TARGET_CONTAINER\"..."
  output=$(docker exec -i "$TARGET_CONTAINER" psql -q -v ON_ERROR_STOP=1 -U "$FILE_POSTGRES_USER" -d "$FILE_POSTGRES_DB" < "$BACKUPS_DIR/$DUMP_FILENAME" 2>&1) || fail "$output"

  RESTORED_COUNTS=$(table_counts "$TARGET_CONTAINER") || fail "Could not read the restored database. The dump is kept at \"postgres/backups/$DUMP_FILENAME\"."
  if [ "$RESTORED_COUNTS" = "$SOURCE_COUNTS" ]; then
    print_info "Restore complete, every table matches: $(format_counts "$RESTORED_COUNTS")"
  else
    print_error "Legacy database: $(format_counts "$SOURCE_COUNTS")"
    print_error "Target database: $(format_counts "$RESTORED_COUNTS")"
    fail "The copy does not match the legacy database. The dump is kept at \"postgres/backups/$DUMP_FILENAME\"."
  fi
  echo ""

  # =============================================================================
  # Section 8: Remove the legacy container
  # =============================================================================

  if [ "$LEGACY_SOURCE" = "container" ]; then
    docker rm -f "$LEGACY_CONTAINER" > /dev/null 2>&1
    print_info "Legacy container \"$LEGACY_CONTAINER\" removed"
  else
    docker rm -f "$TEMP_CONTAINER" > /dev/null 2>&1
    TEMP_CONTAINER_CREATED=false
    print_info "Temporary container \"$TEMP_CONTAINER\" removed"
  fi
  print_warning "The directory \"file-postgres/data\" was left in place. Delete it once you have verified that file uploads and downloads work."
  echo ""

fi

# =============================================================================
# Section 9: Start containers
# =============================================================================

output=$(compose up -d 2>&1) || fail "$output"
print_info "Containers successfully started"

# 9.1 Nginx resolves the file service address once at startup. The file service
# container was recreated above, so reload nginx to pick up its new address.
if docker container inspect "$NGINX_CONTAINER" > /dev/null 2>&1; then
  if docker exec "$NGINX_CONTAINER" nginx -s reload > /dev/null 2>&1; then
    print_info "Nginx configuration reloaded"
  else
    print_warning "Could not reload nginx. If file downloads return 502, run: docker restart $NGINX_CONTAINER"
  fi
fi

echo ""
if [ "$LEGACY_SOURCE" = "none" ]; then
  print_info "Done! Database \"$FILE_POSTGRES_DB\" is ready in \"$TARGET_CONTAINER\". There was nothing to copy."
else
  print_info "Done! The file service database now lives in \"$TARGET_CONTAINER\". Backup of the legacy database: postgres/backups/$DUMP_FILENAME"
fi
echo ""
