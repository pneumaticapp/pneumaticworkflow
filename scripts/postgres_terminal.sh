#!/bin/bash

# =============================================================================
# Open an interactive PostgreSQL terminal inside the pneumatic-postgres container
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ENV_FILE="$SCRIPT_DIR/../.env"

# =============================================================================
# Color output helpers
# =============================================================================

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

print_error() { echo -e "${RED}$1${NC}"; }
print_info()  { echo -e "${GREEN}$1${NC}"; }

# =============================================================================
# Section 1: Read .env file and extract database configuration
# =============================================================================

if [ ! -f "$ENV_FILE" ]; then
  print_error "Error: .env file not found at $ENV_FILE. Cannot proceed without database configuration."
  exit 1
fi

POSTGRES_HOST="postgres"
POSTGRES_USER="postgres_user"
POSTGRES_PASSWORD="postgres_password"
POSTGRES_DB="postgres_db"

while IFS='=' read -r key value || [ -n "$key" ]; do
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
# Section 2: Open interactive psql session
# =============================================================================

print_info "Connecting to database \"$POSTGRES_DB\" as user \"$POSTGRES_USER\"..."
docker exec -e "PGPASSWORD=$POSTGRES_PASSWORD" -it pneumatic-postgres psql -U "$POSTGRES_USER" "$POSTGRES_DB"
