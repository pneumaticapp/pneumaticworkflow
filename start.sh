#!/bin/bash

# Pneumatic Workflow automated startup
set -e

# Always run from the directory containing this script so that all relative
# paths (.env, docker-compose.yml, nginx/, etc.) resolve correctly regardless
# of where the caller invoked start.sh from.
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Prevent environment variable injection: unset all variables that are later
# written into .env via sed. Values must be entered interactively or generated
# by this script — never inherited from the caller's environment.
unset SERVER_ADDRESS
unset DJANGO_SECRET_KEY
unset POSTGRES_PASSWORD REDIS_PASSWORD RABBITMQ_PASSWORD
unset CERTBOT_ENABLE CERTBOT_EMAIL NGINX_CONF_TEMPLATE
unset GIT_BRANCH

RED='\033[0;31m'
ORANGE='\033[0;33m'
GREEN='\033[0;32m'
NC='\033[0m'

print_error()   { echo -e "${RED}$1${NC}"; }
print_warning() { echo -e "${ORANGE}$1${NC}"; }
print_info()    { echo -e "${GREEN}$1${NC}"; }

# =============================================================================
# 0. Prerequisites check
# =============================================================================

# 0.1 Check Docker
if ! command -v docker &>/dev/null; then
    print_error "Docker is not installed or not in PATH. Please install Docker and try again."
    exit 1
fi

# 0.2 Check Docker Compose
if ! docker compose version &>/dev/null; then
    print_error "Docker Compose plugin is not available. Please install Docker Compose and try again."
    exit 1
fi

# 0.3 Check Git
if ! command -v git &>/dev/null; then
    print_error "Git is not installed or not in PATH. Please install Git and try again."
    exit 1
fi

# 0.4 Check write access to script directory
if [ ! -w "$SCRIPT_DIR" ]; then
    print_error "No write permission to $SCRIPT_DIR. Please run the script with appropriate permissions."
    exit 1
fi

GIT_BRANCH=$(git -C "$SCRIPT_DIR" rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")

# =============================================================================
# 1. Create default .env file if not exist
# =============================================================================

ENV_FILE_CREATED=false

if [ ! -f ".env" ]; then

    DEFAULT_ENV="./default.env"
    ENV_FILE="./.env"
    NGINX_CONF_TEMPLATE=./nginx/templates/

    cp "$DEFAULT_ENV" "$ENV_FILE"
    ENV_FILE_CREATED=true
    print_info "Project configuration started"


    # 1.1 Set Required values
    DJANGO_SECRET_KEY=$(cat /dev/urandom | tr -dc 'abcdefghijklmnopqrstuvwxyz0123456789!@%^*()_=+' | head -c 50)
    sed -i "s|^#\?\s*DJANGO_SECRET_KEY=.*|DJANGO_SECRET_KEY=$DJANGO_SECRET_KEY|"                  "$ENV_FILE"

    # =============================================================================
    # 1.2 Set SERVER_ADDRESS
    # =============================================================================

    # 1.2.1 Prompt for SERVER_ADDRESS
    DOMAIN_PATTERN='^([a-zA-Z0-9][a-zA-Z0-9-]*\.)+[a-zA-Z]{2,}$'
    IP_PATTERN='^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'

    while true; do
        read -rp "Enter server address (IP, domain or localhost): " SERVER_ADDRESS
        if [[ "$SERVER_ADDRESS" =~ $DOMAIN_PATTERN ]] || \
           [[ "$SERVER_ADDRESS" =~ $IP_PATTERN ]]     || \
           [ "$SERVER_ADDRESS" = "localhost" ]; then
            break
        else
            print_error "Invalid address. Please enter an IP address, domain name or localhost."
        fi
    done
    print_info "Server address: $SERVER_ADDRESS"

    # 1.2.2 Address type boolean flags
    ADDRESS_IS_DOMAIN=false
    ADDRESS_IS_IP=false
    ADDRESS_IS_LOCALHOST=false

    [[ "$SERVER_ADDRESS" =~ $DOMAIN_PATTERN ]] && ADDRESS_IS_DOMAIN=true
    [[ "$SERVER_ADDRESS" =~ $IP_PATTERN ]]     && ADDRESS_IS_IP=true
    [ "$SERVER_ADDRESS" = "localhost" ]         && ADDRESS_IS_LOCALHOST=true

    # =============================================================================
    # 1.3 Set passwords
    # =============================================================================

    if [ "$ADDRESS_IS_LOCALHOST" = false ]; then
        # 1.3.1 Generate passwords (not needed for localhost)
        POSTGRES_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
        REDIS_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
        RABBITMQ_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)

        # 1.3.2 Write passwords to .env
        sed -i "s|^#\?\s*POSTGRES_PASSWORD=.*|POSTGRES_PASSWORD=$POSTGRES_PASSWORD|"                  "$ENV_FILE"
        sed -i "s|^#\?\s*POSTGRES_REPLICA_PASSWORD=.*|POSTGRES_REPLICA_PASSWORD=$POSTGRES_PASSWORD|"  "$ENV_FILE"
        sed -i "s|^#\?\s*REDIS_PASSWORD=.*|REDIS_PASSWORD=$REDIS_PASSWORD|"                           "$ENV_FILE"
        sed -i "s|^#\?\s*RABBITMQ_PASSWORD=.*|RABBITMQ_PASSWORD=$RABBITMQ_PASSWORD|"                  "$ENV_FILE"
    fi

    # =============================================================================
    # 1.4 Set SSL
    # =============================================================================

    SSL=false
    CERTBOT_ENABLE=false

    # 1.4.1 Prompt to enable SSL if SERVER_ADDRESS is a domain
    if [ "$ADDRESS_IS_DOMAIN" = true ]; then
        while true; do
            read -rp "Enable SSL for $SERVER_ADDRESS? A free Let's Encrypt certificate will be used [y/n]: " ssl_choice
            case "$ssl_choice" in
                [Yy]|[Yy][Ee][Ss]) SSL=true;  CERTBOT_ENABLE=true;  break ;;
                [Nn]|[Nn][Oo])     SSL=false; CERTBOT_ENABLE=false; break ;;
                *) print_error "Please answer yes (y) or no (n)." ;;
            esac
        done
        [ "$SSL" = true ] && print_info "SSL enabled"
    fi

    # 1.4.2 Prompt for CERTBOT_EMAIL if SSL is enabled
    if [ "$CERTBOT_ENABLE" = true ]; then
        NGINX_CONF_TEMPLATE=./nginx/ssl_templates/
        EMAIL_PATTERN='^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$'
        while true; do
            read -rp "Enter email for free Let's Encrypt SSL certificate: " CERTBOT_EMAIL
            if [[ "$CERTBOT_EMAIL" =~ $EMAIL_PATTERN ]]; then
                break
            else
                print_error "Invalid email address. Please try again."
            fi
        done
    fi

    # 1.4.3 Write SSL settings to .env
    _ssl_value="no"
    [ "$SSL" = true ] && _ssl_value="yes"
    _certbot_enable_value="no"
    [ "$CERTBOT_ENABLE" = true ] && _certbot_enable_value="yes"
    sed -i "s|^#\?\s*SSL=.*|SSL=$_ssl_value|"                                                       "$ENV_FILE"
    sed -i "s|^#\?\s*CERTBOT_ENABLE=.*|CERTBOT_ENABLE=$_certbot_enable_value|"                     "$ENV_FILE"
    sed -i "s|^#\?\s*CERTBOT_EMAIL=.*|CERTBOT_EMAIL=$CERTBOT_EMAIL|"                               "$ENV_FILE"
    sed -i "s|^#\?\s*NGINX_CONF_TEMPLATE=.*|NGINX_CONF_TEMPLATE=$NGINX_CONF_TEMPLATE|"             "$ENV_FILE"

    print_info "Setup completed successfully"
    # =============================================================================
    # 1.5 Write SERVER_ADDRESS and URLs to .env
    # =============================================================================

    # 1.5.1 Set protocol variables
    HTTP_PROTOCOL=http
    WS_PROTOCOL=ws
    [ "$CERTBOT_ENABLE" = true ] && HTTP_PROTOCOL=https
    [ "$CERTBOT_ENABLE" = true ] && WS_PROTOCOL=wss

    sed -i "s|^#\?\s*SERVER_ADDRESS=.*|SERVER_ADDRESS=$SERVER_ADDRESS|"                             "$ENV_FILE"
    sed -i "s|^#\?\s*BACKEND_URL=.*|BACKEND_URL=$HTTP_PROTOCOL://$SERVER_ADDRESS:8001|"             "$ENV_FILE"
    sed -i "s|^#\?\s*FRONTEND_URL=.*|FRONTEND_URL=$HTTP_PROTOCOL://$SERVER_ADDRESS|"                "$ENV_FILE"
    sed -i "s|^#\?\s*FORM_DOMAIN=.*|FORM_DOMAIN=form.$SERVER_ADDRESS|"                              "$ENV_FILE"
    sed -i "s|^#\?\s*WSS_URL=.*|WSS_URL=$WS_PROTOCOL://$SERVER_ADDRESS:8001|"                       "$ENV_FILE"

fi

# =============================================================================
# 2. Start Docker containers
# =============================================================================


# 2.1 Select docker-compose configuration
echo ""
print_info "Select a version to start:"
echo ""
echo "  1. Stable (recommended)"
echo "  2. Latest"
echo "  3. From sources (Branch: \"$GIT_BRANCH\")"
echo ""

while true; do
    read -r -p "Enter number (1-3): " COMPOSE_FILE

    if ! [[ "$COMPOSE_FILE" =~ ^[0-9]+$ ]]; then
        print_error "Please enter a number."
        continue
    fi

    if [ "$COMPOSE_FILE" -lt 1 ] || [ "$COMPOSE_FILE" -gt 3 ]; then
        print_error "Please enter 1, 2 or 3."
        continue
    fi

    break
done

case "$COMPOSE_FILE" in
  1) COMPOSE_LABEL="Stable (recommended)";   COMPOSE_ARGS=('-f' 'docker-compose.yml');     COMPOSE_TAG="stable" ;;
  2) COMPOSE_LABEL="Latest";                 COMPOSE_ARGS=('-f' 'docker-compose.yml');     COMPOSE_TAG="latest" ;;
  3) COMPOSE_LABEL="From sources (Branch: \"$GIT_BRANCH\")"; COMPOSE_ARGS=('-f' 'docker-compose.src.yml'); COMPOSE_TAG=""   ;;
esac

echo ""
print_info "Selected configuration: $COMPOSE_LABEL"
echo ""


# 2.2 Stop running containers
echo "Stopping existing containers..."
docker compose "${COMPOSE_ARGS[@]}" down

# 2.3 Start containers

echo ""
echo "Starting Docker containers..."

if [ -n "$COMPOSE_TAG" ]; then
    output=$(TAG="$COMPOSE_TAG" docker compose "${COMPOSE_ARGS[@]}" up -d 2>&1)
else
    output=$(docker compose "${COMPOSE_ARGS[@]}" up -d 2>&1)
fi
if [ $? -eq 0 ]; then
  print_info "Containers successfully started"
else
  print_error "$output"
  exit 1
fi

# =============================================================================
# 3. Summary
# =============================================================================

echo ""
echo "Pneumatic Workflow started successfully!"
echo ""
echo "Please wait a few minutes for all services to fully start"
echo ""
