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
unset FORM_DOMAIN
unset GIT_BRANCH

RED='\033[0;31m'
ORANGE='\033[0;33m'
GREEN='\033[0;32m'
NC='\033[0m'

print_error()   { echo -e "${RED}$1${NC}"; }
print_warning() { echo -e "${ORANGE}$1${NC}"; }
print_info()    { echo -e "${GREEN}$1${NC}"; }

echo ""
echo -e "${ORANGE}"
echo "  ██████╗ ███╗   ██╗███████╗██╗   ██╗███╗   ███╗ █████╗ ████████╗██╗ ██████╗ "
echo "  ██╔══██╗████╗  ██║██╔════╝██║   ██║████╗ ████║██╔══██╗╚══██╔══╝██║██╔════╝ "
echo "  ██████╔╝██╔██╗ ██║█████╗  ██║   ██║██╔████╔██║███████║   ██║   ██║██║      "
echo "  ██╔═══╝ ██║╚██╗██║██╔══╝  ██║   ██║██║╚██╔╝██║██╔══██║   ██║   ██║██║      "
echo "  ██║     ██║ ╚████║███████╗╚██████╔╝██║ ╚═╝ ██║██║  ██║   ██║   ██║╚██████╗ "
echo "  ╚═╝     ╚═╝  ╚═══╝╚══════╝ ╚═════╝ ╚═╝     ╚═╝╚═╝  ╚═╝   ╚═╝   ╚═╝ ╚═════╝"
echo -e "${NC}"

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

    # 1.1 Create new .env file from default
    DEFAULT_ENV="./default.env"
    ENV_FILE="./.env"
    NGINX_CONF_TEMPLATE=./nginx/templates/

    cp "$DEFAULT_ENV" "$ENV_FILE"
    ENV_FILE_CREATED=true
    print_info "Project configuration started"
    echo ""

    # 1.2 Create DJANGO_SECRET_KEY
    DJANGO_SECRET_KEY=$(cat /dev/urandom | tr -dc 'abcdefghijklmnopqrstuvwxyz0123456789!@%^*()_=+' | head -c 50)
    sed -i "s|^#\?\s*DJANGO_SECRET_KEY=.*|DJANGO_SECRET_KEY=$DJANGO_SECRET_KEY|"                  "$ENV_FILE"

    # 1.3 Prompt server address
    DOMAIN_PATTERN='^([a-zA-Z0-9][a-zA-Z0-9-]*\.)+[a-zA-Z]{2,}$'
    IP_PATTERN='^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'

    while true; do
        read -rp "Enter server address (IP, domain or localhost): " SERVER_ADDRESS
        if [[ "$SERVER_ADDRESS" =~ $DOMAIN_PATTERN ]] || \
           [[ "$SERVER_ADDRESS" =~ $IP_PATTERN ]]     || \
           [ "$SERVER_ADDRESS" = "localhost" ]        || \
           [ "$SERVER_ADDRESS" = "127.0.0.1" ]; then
            break
        else
            print_error "Invalid address. Please enter an IP address, domain name or localhost."
        fi
    done
    print_info "Server address: $SERVER_ADDRESS"

    # 1.3.2 Set address type boolean flags
    ADDRESS_IS_DOMAIN=false
    ADDRESS_IS_IP=false
    ADDRESS_IS_LOCALHOST=false

    if [ "$SERVER_ADDRESS" = "localhost" ] || [ "$SERVER_ADDRESS" = "127.0.0.1" ]; then
        ADDRESS_IS_LOCALHOST=true
    elif [[ "$SERVER_ADDRESS" =~ $DOMAIN_PATTERN ]]; then
        ADDRESS_IS_DOMAIN=true
    elif [[ "$SERVER_ADDRESS" =~ $IP_PATTERN ]]; then
        ADDRESS_IS_IP=true
    fi

    # 1.4 Sharable kickoff forms domain
    FORM_DOMAIN=""
    if [ "$ADDRESS_IS_DOMAIN" = true ]; then
        echo ""
        read -rp "Use default address for Sharable kickoff forms ($SERVER_ADDRESS/forms)? [Y/n]: " forms_choice
        case "$forms_choice" in
            [Nn]|[Nn][Oo])
                # 1.2.4 Prompt for a separate kickoff forms domain
                while true; do
                    read -rp "Enter domain for Sharable kickoff forms (e.g. forms.example.com): " FORM_DOMAIN
                    if [[ "$FORM_DOMAIN" =~ $DOMAIN_PATTERN ]]; then
                        break
                    else
                        print_error "Invalid domain. Please enter a valid domain name (e.g. forms.example.com)."
                    fi
                done
                print_info "Kickoff forms domain: $FORM_DOMAIN"
                ;;
            *)
                print_info "Kickoff forms will be served at: $SERVER_ADDRESS/forms"
                ;;
        esac
        if [ -n "$FORM_DOMAIN" ]; then
            sed -i "s|^#\?\s*FORM_DOMAIN=.*|FORM_DOMAIN=$FORM_DOMAIN|" "$ENV_FILE"
        fi
    fi

    # 1.5 Passwords
    if [ "$ADDRESS_IS_LOCALHOST" = false ]; then

        # 1.5.1 Generate passwords (not needed for localhost)
        POSTGRES_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
        REDIS_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
        RABBITMQ_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)

        # 1.5.2 Write passwords to .env
        sed -i "s|^#\?\s*POSTGRES_PASSWORD=.*|POSTGRES_PASSWORD=$POSTGRES_PASSWORD|"                  "$ENV_FILE"
        sed -i "s|^#\?\s*POSTGRES_REPLICA_PASSWORD=.*|POSTGRES_REPLICA_PASSWORD=$POSTGRES_PASSWORD|"  "$ENV_FILE"
        sed -i "s|^#\?\s*REDIS_PASSWORD=.*|REDIS_PASSWORD=$REDIS_PASSWORD|"                           "$ENV_FILE"
        sed -i "s|^#\?\s*RABBITMQ_PASSWORD=.*|RABBITMQ_PASSWORD=$RABBITMQ_PASSWORD|"                  "$ENV_FILE"
    fi

    # 1.6 SSL
    SSL=false
    CERTBOT_ENABLE=false

    # 1.6.1 Prompt to enable SSL if SERVER_ADDRESS is a domain
    if [ "$ADDRESS_IS_DOMAIN" = true ]; then
        echo ""
        while true; do
            read -rp "Enable SSL for $SERVER_ADDRESS? A free Let's Encrypt certificate will be used [y/n]: " ssl_choice
            case "$ssl_choice" in
                [Yy]|[Yy][Ee][Ss]) SSL=true;  CERTBOT_ENABLE=true;  break ;;
                [Nn]|[Nn][Oo])     SSL=false; CERTBOT_ENABLE=false; break ;;
                *) print_error "Please answer yes (y) or no (n)." ;;
            esac
        done
        [ "$SSL" = true ] && print_info "SSL enabled"

        # 1.6.2 Write SSL to .env
        _ssl_value="no"
        [ "$SSL" = true ] && _ssl_value="yes"
        sed -i "s|^#\?\s*SSL=.*|SSL=$_ssl_value|" "$ENV_FILE"

        # 1.6.3 Write $CERTBOT_ENABLE to .env
        _certbot_enable_value="no"
        [ "$CERTBOT_ENABLE" = true ] && _certbot_enable_value="yes"
        sed -i "s|^#\?\s*CERTBOT_ENABLE=.*|CERTBOT_ENABLE=$_certbot_enable_value|" "$ENV_FILE"

    fi

    # 1.7 Prompt for CERTBOT_EMAIL if SSL is enabled
    if [ "$CERTBOT_ENABLE" = true ]; then
        EMAIL_PATTERN='^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$'
        echo ""
        while true; do
            read -rp "Enter email for registration free Let's Encrypt SSL certificate: " CERTBOT_EMAIL
            if [[ "$CERTBOT_EMAIL" =~ $EMAIL_PATTERN ]]; then
                break
            else
                print_error "Invalid email address. Please try again."
            fi
        done
        print_info "Let's Encrypt certificate will be registered to: $CERTBOT_EMAIL"

        # 1.7.1  Write $CERTBOT_EMAIL to .env
        sed -i "s|^#\?\s*CERTBOT_EMAIL=.*|CERTBOT_EMAIL=$CERTBOT_EMAIL|" "$ENV_FILE"
    fi

    # 1.8 Set Nginx conf template
    if [ "$CERTBOT_ENABLE" = true ] && [ -n "$FORM_DOMAIN" ]; then
        NGINX_CONF_TEMPLATE=./nginx/ssl_forms_templates/
    elif [ "$CERTBOT_ENABLE" = true ]; then
        NGINX_CONF_TEMPLATE=./nginx/ssl_templates/
    else
        NGINX_CONF_TEMPLATE=./nginx/templates/
    fi
    sed -i "s|^#\?\s*NGINX_CONF_TEMPLATE=.*|NGINX_CONF_TEMPLATE=$NGINX_CONF_TEMPLATE|" "$ENV_FILE"

    echo ""
    print_info "Setup completed"

    # 1.9 Set protocol variables
    HTTP_PROTOCOL=http
    WS_PROTOCOL=ws
    [ "$CERTBOT_ENABLE" = true ] && HTTP_PROTOCOL=https
    [ "$CERTBOT_ENABLE" = true ] && WS_PROTOCOL=wss

    # 1.10 Write addresses and URLs to .env
    sed -i "s|^#\?\s*SERVER_ADDRESS=.*|SERVER_ADDRESS=$SERVER_ADDRESS|"                   "$ENV_FILE"
    sed -i "s|^#\?\s*BACKEND_URL=.*|BACKEND_URL=$HTTP_PROTOCOL://$SERVER_ADDRESS:8001|"   "$ENV_FILE"
    sed -i "s|^#\?\s*FRONTEND_URL=.*|FRONTEND_URL=$HTTP_PROTOCOL://$SERVER_ADDRESS|"      "$ENV_FILE"
    sed -i "s|^#\?\s*WSS_URL=.*|WSS_URL=$WS_PROTOCOL://$SERVER_ADDRESS:8001|"             "$ENV_FILE"

    # 1.11 Write forms url to .env
    if [ -n "$FORM_DOMAIN" ]; then
        FORMS_URL="$HTTP_PROTOCOL://$FORM_DOMAIN"
    else
        FORMS_URL="$HTTP_PROTOCOL://$SERVER_ADDRESS/forms"
    fi
    sed -i "s|^#\?\s*FORMS_URL=.*|FORMS_URL=$FORMS_URL|"  "$ENV_FILE"


fi

# =============================================================================
# 2. Start Docker containers
# =============================================================================

# 2.1 Select docker-compose configuration
echo ""
echo "Select a version to start:"
echo "  1. Stable (recommended)"
echo "  2. Latest"
echo "  3. From sources (Branch: \"$GIT_BRANCH\")"

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

print_info "Selected configuration: $COMPOSE_LABEL"
echo ""

# 2.2 Start containers

echo "Starting Docker containers..."

if [ -n "$COMPOSE_TAG" ]; then
    output=$(TAG="$COMPOSE_TAG" docker compose "${COMPOSE_ARGS[@]}" up -d 2>&1)
else
    output=$(docker compose "${COMPOSE_ARGS[@]}" up -d 2>&1)
fi
if [ $? -eq 0 ]; then
  print_info "Done"
else
  print_error "$output"
  exit 1
fi

# =============================================================================
# 3. Summary
# =============================================================================

# Read FRONTEND_URL from .env if not already set (e.g. on repeated runs)
if [ -z "$FRONTEND_URL" ] && [ -f ".env" ]; then
    FRONTEND_URL=$(grep -E '^FRONTEND_URL=' .env | cut -d'=' -f2-)
fi

echo ""
echo "Pneumatic Workflow started successfully!"
echo "The application is available at $FRONTEND_URL"
print_warning "Please wait a few minutes for all services to fully start"
print_warning ""

if [ "$CERTBOT_ENABLE" = true ]; then
    print_warning "SSL Let's Encrypt certificate was not created automatically. This feature will be available in the next patch."
    print_warning "Install certbot on the host machine and copy the certificates to the nginx/keys/your-domain/ directory."
fi

echo ""
