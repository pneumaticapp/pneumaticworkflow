#!/bin/bash

# =============================================================================
# Restore a PostgreSQL backup from the "postgres/backups" directory
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKUPS_DIR="$SCRIPT_DIR/../postgres/backups"
ENV_FILE="$SCRIPT_DIR/../.env"

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

# =============================================================================
# Section 1: Scan backup directory and display file list
# =============================================================================

files=()
if [ -d "$BACKUPS_DIR" ]; then
  while IFS= read -r -d '' file; do
    files+=("$(basename "$file")")
  done < <(find "$BACKUPS_DIR" -maxdepth 1 -type f -print0 | sort -z)
fi

if [ ${#files[@]} -eq 0 ]; then
  print_warning 'No backup files were found in the "postgres/backups" directory.'
  exit 0
fi

print_info "Available backup files:"
echo ""
for i in "${!files[@]}"; do
  echo "  $((i + 1)). ${files[$i]}"
done
echo ""

# =============================================================================
# Section 2: User selects a backup file by number
# =============================================================================

while true; do
  read -r -p "Select a backup file and enter its number (1-${#files[@]}): " choice

  if ! [[ "$choice" =~ ^[0-9]+$ ]]; then
    print_error "Enter the file number"
    continue
  fi

  if [ "$choice" -lt 1 ] || [ "$choice" -gt ${#files[@]} ]; then
    print_error "Entered number does not match any file from the list"
    continue
  fi

  BACKUP_FILENAME="${files[$((choice - 1))]}"
  break
done

echo ""
print_info "Selected file: $BACKUP_FILENAME"
echo ""

# =============================================================================
# Section 3: Read .env file and extract database configuration
# =============================================================================

if [ ! -f "$ENV_FILE" ]; then
  print_error "Error: .env file not found at $ENV_FILE. Cannot proceed without database configuration."
  exit 1
fi

POSTGRES_HOST="postgres"
POSTGRES_USER="postgres_user"
POSTGRES_PASSWORD="postgres_password"
POSTGRES_DB="postgres_db"

while IFS='=' read -r key value; do
  key=$(echo "$key" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
  value=$(echo "$value" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')

  [ -z "$key" ] && continue
  [[ "$key" == \#* ]] && continue

  value=$(echo "$value" | sed 's/[[:space:]]\+#.*$//;s/[[:space:]]*$//')

  case "$key" in
    POSTGRES_HOST)     POSTGRES_HOST="$value" ;;
    POSTGRES_USER)     POSTGRES_USER="$value" ;;
    POSTGRES_PASSWORD) POSTGRES_PASSWORD="$value" ;;
    POSTGRES_DB)       POSTGRES_DB="$value" ;;
  esac
done < "$ENV_FILE"

# =============================================================================
# Section 3.1: Confirm database overwrite
# =============================================================================

while true; do
  print_warning "WARNING: This action will overwrite the database \"$POSTGRES_DB\"."
  read -r -p "Continue? (y/n): " confirm

  case "$confirm" in
    y) break ;;
    n) print_warning "Operation cancelled."; exit 0 ;;
    *) ;;
  esac
done

echo ""

PROJECT_DIR="$SCRIPT_DIR/.."

# =============================================================================
# Section 4: Prepare containers
# =============================================================================

# 4.1 Stop all pneumatic containers
output=$(docker compose -f "$PROJECT_DIR/docker-compose.yml" down 2>&1)
if [ $? -eq 0 ]; then
  print_info "Containers successfully removed"
else
  print_error "$output"
  exit 1
fi

# 4.2 Start the postgres container
output=$(docker compose -f "$PROJECT_DIR/docker-compose.src.yml" up -d postgres 2>&1)
if [ $? -eq 0 ]; then
  print_info "Container \"postgres\" is running"
else
  print_error "$output"
  exit 1
fi

# =============================================================================
# Section 5: Drop, recreate, and restore the database
# =============================================================================

# 5.1 Wait for the database to become available
print_info "Waiting for the database to become available..."
MAX_RETRIES=30
RETRY_COUNT=0
while true; do
  docker exec pneumatic-postgres pg_isready -U "$POSTGRES_USER" -h "$POSTGRES_HOST" > /dev/null 2>&1
  if [ $? -eq 0 ]; then
    print_info "Database is ready"
    break
  fi

  RETRY_COUNT=$((RETRY_COUNT + 1))
  if [ "$RETRY_COUNT" -ge "$MAX_RETRIES" ]; then
    print_error "Database is not available after ${MAX_RETRIES} seconds"
    exit 1
  fi

  sleep 1
done

# 5.2 Drop the existing database
output=$(docker exec -e "PGPASSWORD=$POSTGRES_PASSWORD" pneumatic-postgres dropdb -U "$POSTGRES_USER" "$POSTGRES_DB" 2>&1)
if [ $? -eq 0 ]; then
  print_info "Database successfully dropped"
else
  print_error "$output"
  exit 1
fi

# 5.3 Create a new database
output=$(docker exec -e "PGPASSWORD=$POSTGRES_PASSWORD" pneumatic-postgres createdb -U "$POSTGRES_USER" --owner "$POSTGRES_USER" "$POSTGRES_DB" 2>&1)
if [ $? -eq 0 ]; then
  print_info "Database successfully created"
else
  print_error "$output"
  exit 1
fi

# 5.4 Restore from backup
print_info "Restoring database \"$POSTGRES_DB\" from file \"$BACKUP_FILENAME\", this may take a few minutes..."
output=$(docker exec -i -e "PGPASSWORD=$POSTGRES_PASSWORD" pneumatic-postgres psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -h "$POSTGRES_HOST" "$POSTGRES_DB" < "$BACKUPS_DIR/$BACKUP_FILENAME" 2>&1)
if [ $? -eq 0 ]; then
  print_info "Backup successfully restored"
else
  print_error "$output"
  exit 1
fi

# =============================================================================
# Section 6: Start containers
# =============================================================================

# 6.1 Ask user which docker-compose configuration to use
echo ""
print_info "Select a docker-compose configuration to start containers:"
echo ""
echo "  1. Root (latest)"
echo "  2. Root (stable)"
echo "  3. Root (from sources)"
echo "  4. Frontend"
echo "  5. Backend"
echo ""

# 6.2 User selects a configuration by number
while true; do
  read -r -p "Enter configuration number (1-5): " COMPOSE_FILE

  if ! [[ "$COMPOSE_FILE" =~ ^[0-9]+$ ]]; then
    print_error "Enter the file number"
    continue
  fi

  if [ "$COMPOSE_FILE" -lt 1 ] || [ "$COMPOSE_FILE" -gt 5 ]; then
    print_error "Entered number does not match any file from the list"
    continue
  fi

  break
done

echo ""

# 6.3 Run the selected docker-compose command
case "$COMPOSE_FILE" in
  1)
    output=$(TAG=latest docker compose -f "$PROJECT_DIR/docker-compose.yml" up -d 2>&1)
    ;;
  2)
    output=$(TAG=stable docker compose -f "$PROJECT_DIR/docker-compose.yml" up -d 2>&1)
    ;;
  3)
    output=$(docker compose -f "$PROJECT_DIR/docker-compose.src.yml" up -d 2>&1)
    ;;
  4)
    output=$(docker compose -f "$PROJECT_DIR/frontend/docker-compose.yml" up -d 2>&1)
    ;;
  5)
    output=$(docker compose -f "$PROJECT_DIR/backend/docker-compose.yml" up -d 2>&1)
    ;;
esac

if [ $? -eq 0 ]; then
  print_info "Containers successfully started"
else
  print_error "$output"
  exit 1
fi

echo ""
print_info "Done! Database \"$POSTGRES_DB\" has been successfully restored from \"$BACKUP_FILENAME\"."

echo ""
echo -e "${GREEN}"
cat << 'EOF'
                    __
                   '. \
                    '- \
                     / /_         .---.
                    / | \\,.\/--.//    )
                    |  \//        )/  /
                     \  ' ^ ^    /    )
                      '.____.    .___/ 
                         .\  \   |  /
                           \______/
                             Done!
EOF
echo -e "${NC}"
