#!/bin/bash

# Pneumatic Workflow automated startup
set -e

RED='\033[0;31m'
ORANGE='\033[0;33m'
GREEN='\033[0;32m'
NC='\033[0m'

print_error()   { echo -e "${RED}$1${NC}"; }
print_warning() { echo -e "${ORANGE}$1${NC}"; }
print_info()    { echo -e "${GREEN}$1${NC}"; }

# =============================================================================
# 1. Create default .env file if not exist
# =============================================================================

ENV_FILE_CREATED=false

if [ ! -f ".env" ]; then

    SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
    DEFAULT_ENV="$SCRIPT_DIR/default.env"
    ENV_FILE="$SCRIPT_DIR/.env"

    cp "$DEFAULT_ENV" "$ENV_FILE"
    ENV_FILE_CREATED=true
    print_info ".env created from default.env"


    # =============================================================================
    # 1.2 Set SERVER_ADDRESS
    # =============================================================================

    # 1.2.1 Prompt for SERVER_ADDRESS
    DOMAIN_PATTERN='^([a-zA-Z0-9][a-zA-Z0-9-]*\.)+[a-zA-Z]{2,}$'
    IP_PATTERN='^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'

    if [ -z "$SERVER_ADDRESS" ]; then
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
    fi

    # 1.2.2 Address type boolean flags
    ADDRESS_IS_DOMAIN=false
    ADDRESS_IS_IP=false
    ADDRESS_IS_LOCALHOST=false

    [[ "$SERVER_ADDRESS" =~ $DOMAIN_PATTERN ]] && ADDRESS_IS_DOMAIN=true
    [[ "$SERVER_ADDRESS" =~ $IP_PATTERN ]]     && ADDRESS_IS_IP=true
    [ "$SERVER_ADDRESS" = "localhost" ]         && ADDRESS_IS_LOCALHOST=true

    # 1.2.3 Write SERVER_ADDRESS and URLs to .env
    sed -i "s|^#\?\s*SERVER_ADDRESS=.*|SERVER_ADDRESS=$SERVER_ADDRESS|"        "$ENV_FILE"
    sed -i "s|^#\?\s*BACKEND_URL=.*|BACKEND_URL=http://$SERVER_ADDRESS:8001|"  "$ENV_FILE"
    sed -i "s|^#\?\s*FRONTEND_URL=.*|FRONTEND_URL=http://$SERVER_ADDRESS|"     "$ENV_FILE"
    sed -i "s|^#\?\s*FORMS_URL=.*|FORMS_URL=http://form.$SERVER_ADDRESS|"      "$ENV_FILE"
    sed -i "s|^#\?\s*FRONTEND_DOMAIN=.*|FRONTEND_DOMAIN=$SERVER_ADDRESS|"      "$ENV_FILE"
    sed -i "s|^#\?\s*BACKEND_DOMAIN=.*|BACKEND_DOMAIN=$SERVER_ADDRESS|"        "$ENV_FILE"
    sed -i "s|^#\?\s*FORM_DOMAIN=.*|FORM_DOMAIN=form.$SERVER_ADDRESS|"         "$ENV_FILE"
    sed -i "s|^#\?\s*WSS_URL=.*|WSS_URL=ws://$SERVER_ADDRESS:8001|"            "$ENV_FILE"

    # =============================================================================
    # 1.3 Set passwords
    # =============================================================================

    if [ "$ADDRESS_IS_LOCALHOST" = false ]; then
        # 3.1 Generate missing passwords (not needed for localhost)
        if [ -z "$POSTGRES_PASSWORD" ]; then
            POSTGRES_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
            print_info "Postgres password generated"
        fi

        if [ -z "$REDIS_PASSWORD" ]; then
            REDIS_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
            print_info "Redis password generated"
        fi

        if [ -z "$RABBITMQ_PASSWORD" ]; then
            RABBITMQ_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
            print_info "RabbitMQ password generated"
        fi

        # 3.2 Write passwords to .env
        sed -i "s|^#\?\s*POSTGRES_PASSWORD=.*|POSTGRES_PASSWORD=$POSTGRES_PASSWORD|"                  "$ENV_FILE"
        sed -i "s|^#\?\s*POSTGRES_REPLICA_PASSWORD=.*|POSTGRES_REPLICA_PASSWORD=$POSTGRES_PASSWORD|"  "$ENV_FILE"
        sed -i "s|^#\?\s*REDIS_PASSWORD=.*|REDIS_PASSWORD=$REDIS_PASSWORD|"                           "$ENV_FILE"
        sed -i "s|^#\?\s*RABBITMQ_PASSWORD=.*|RABBITMQ_PASSWORD=$RABBITMQ_PASSWORD|"                  "$ENV_FILE"
    fi

    # =============================================================================
    # 1.4 Set SSL
    # =============================================================================
    if [ "$ADDRESS_IS_LOCALHOST" = false ]; then
        # 4.1 Prompt to enable SSL if SERVER_ADDRESS is a domain
        if [ "$ADDRESS_IS_DOMAIN" = true ]; then
            if [ -z "$CERTBOT_ENABLE" ]; then
                while true; do
                    read -rp "Enable SSL with Let's Encrypt? [Y/n]: " ssl_choice
                    ssl_choice="${ssl_choice:-Y}"
                    case "$ssl_choice" in
                        [Yy]|[Yy][Ee][Ss]) CERTBOT_ENABLE=true;  break ;;
                        [Nn]|[Nn][Oo])     CERTBOT_ENABLE=false; break ;;
                        *) print_error "Please answer yes or no." ;;
                    esac
                done
            fi
        else
            CERTBOT_ENABLE=false
        fi

        # 4.2 Prompt for CERTBOT_EMAIL if SSL is enabled
        if [ "$CERTBOT_ENABLE" = true ]; then
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

        # 4.3 Write SSL settings to .env
        _certbot_enable_value="no"
        [ "$CERTBOT_ENABLE" = true ] && _certbot_enable_value="yes"
        sed -i "s|^#\?\s*CERTBOT_ENABLE=.*|CERTBOT_ENABLE=$_certbot_enable_value|" "$ENV_FILE"
        sed -i "s|^#\?\s*CERTBOT_EMAIL=.*|CERTBOT_EMAIL=$CERTBOT_EMAIL|"           "$ENV_FILE"

        print_info "Setup completed successfully"

    fi
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
echo "  3. From sources (custom branch)"
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
  1) COMPOSE_LABEL="Stable (recommended)" ;;
  2) COMPOSE_LABEL="Latest" ;;
  3) COMPOSE_LABEL="From sources (custom branch)" ;;
esac

echo ""
print_info "Selected configuration: $COMPOSE_LABEL"
echo ""


# 2.2 Stop running containers
echo "Stopping existing containers..."
docker compose down

# 2.3 Start containers

echo ""
echo "Starting Docker containers..."

case "$COMPOSE_FILE" in
  1)
    output=$(TAG=stable docker compose -f "docker-compose.yml" up -d 2>&1)
    ;;
  2)
    output=$(TAG=latest docker compose -f "docker-compose.yml" up -d 2>&1)
    ;;
  3)
    output=$(docker compose -f "docker-compose.src.yml" up -d 2>&1)
    ;;
esac
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
echo "http://$SERVER_ADDRESS"
echo ""
echo "Please wait a few minutes for all services to fully start"
echo "Check status: docker compose ps"
echo "View logs: docker compose logs -f"