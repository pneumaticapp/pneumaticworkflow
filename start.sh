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
unset MCP_SECRET
unset POSTGRES_PASSWORD REDIS_PASSWORD RABBITMQ_PASSWORD
unset CERTBOT_ENABLE CERTBOT_EMAIL NGINX_CONF_TEMPLATE
unset FORM_DOMAIN
unset GIT_BRANCH
unset LOGS_ENABLE LOGS_BACKEND
unset LOGS_OTLP_EXPORT_ENDPOINT LOGS_OTLP_EXPORT_AUTH
unset LOGS_ELASTICSEARCH_URL LOGS_ELASTICSEARCH_API_KEY LOGS_ELASTICSEARCH_USER LOGS_ELASTICSEARCH_PASSWORD
unset MCP_ENABLE
# Compose prefers COMPOSE_PROFILES from the environment over .env; .env must be the only source
unset COMPOSE_PROFILES

RED='\033[0;31m'
ORANGE='\033[0;33m'
GREEN='\033[0;32m'
NC='\033[0m'

print_error()   { echo -e "${RED}$1${NC}"; }
print_warning() { echo -e "${ORANGE}$1${NC}"; }
print_info()    { echo -e "${GREEN}$1${NC}"; }

gen_password() {
    openssl rand -base64 "${1:-32}" | tr -d "=+/" | cut -c1-"${2:-25}"
}

set_env_var() {
    local name="$1" value="$2" escaped
    if grep -qE "^#?\s*${name}=" "$ENV_FILE"; then
        # Values typed by the user may contain characters special to the sed replacement
        escaped=$(printf '%s' "$value" | sed 's/[\\|&]/\\&/g')
        sed -i "s|^#\?\s*${name}=.*|${name}=${escaped}|" "$ENV_FILE"
    else
        [ -z "$(tail -c1 "$ENV_FILE")" ] || echo "" >> "$ENV_FILE"
        echo "${name}=${value}" >> "$ENV_FILE"
    fi
}

# Applies NAME=VALUE pairs to a copy of .env and replaces .env in one mv,
# so an interrupted run leaves .env either untouched or fully updated.
write_env_vars() {
    local target="$ENV_FILE" pair
    _env_tmp="$target.tmp.$$"
    trap 'rm -f "$_env_tmp"' EXIT
    cp -p "$target" "$_env_tmp"
    local ENV_FILE="$_env_tmp"
    for pair in "$@"; do
        set_env_var "${pair%%=*}" "${pair#*=}"
    done
    mv "$_env_tmp" "$target"
    trap - EXIT
}

# read that exits on EOF: inside `if` and `while` conditions set -e does not apply
prompt_value() {
    local _input
    if ! IFS= read -r -p "$2" _input; then
        echo ""
        print_error "Input aborted, nothing was saved for this step."
        exit 1
    fi
    printf -v "$1" '%s' "$(strip_invisible "$_input")"
}

ask_yes_no() {
    local _answer
    while true; do
        prompt_value _answer "$1 [y/n]: "
        case "$_answer" in
            [Yy]|[Yy][Ee][Ss]) return 0 ;;
            [Nn]|[Nn][Oo])     return 1 ;;
            *) print_error "Please answer yes (y) or no (n)." ;;
        esac
    done
}

read_env_value() {
    grep -E "^\s*$1=" "$ENV_FILE" 2>/dev/null | tail -1 | cut -d= -f2- | sed 's/#.*//' | tr -d '"'"'"'[:space:]'
}

strip_invisible() {
    local s
    # Remove ANSI/VT escape sequences (e.g. bracket paste mode: \e[200~ ... \e[201~)
    s=$(printf '%s' "$1" | sed 's/\x1b\[[0-9;?]*[A-Za-z~]//g')
    # Remove leading and trailing whitespace and control characters (CR, BOM, etc.)
    s=$(printf '%s' "$s" | LC_ALL=C sed 's/^[[:space:][:cntrl:]]*//; s/[[:space:][:cntrl:]]*$//')
    printf '%s' "$s"
}

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
# 1. Configuration status checks
# =============================================================================

if [ -f ".env" ]; then

    if grep -q "^SETUP_INCOMPLETE=yes" ".env"; then

        # 1.1 Setup was interrupted
        print_error "Previous setup was interrupted. The .env file is incomplete."
        echo ""
        echo "  1. Delete .env and restart setup (recommended)"
        echo "  2. Exit and edit .env manually"
        read -rp "Enter number (1-2): " INCOMPLETE_CHOICE
        INCOMPLETE_CHOICE=$(strip_invisible "$INCOMPLETE_CHOICE")
        case "$INCOMPLETE_CHOICE" in
            1)
                rm ".env"
                print_info "Restarting setup..."
                exec bash "$0"
                ;;
            *)
                print_warning "Exiting. Edit .env manually, then run the script again."
                exit 0
                ;;
        esac

    else

        # 1.2 Setup already complete (repeated run)
        print_info "To change the current configuration, edit the .env file manually following the instructions:"
        echo "https://github.com/pneumaticapp/pneumaticworkflow/wiki/Configuration"

    fi

fi

# =============================================================================
# 2. Create default .env file if not exist
# =============================================================================

ENV_FILE_CREATED=false
ENV_FILE="./.env"

if [ ! -f ".env" ]; then

    # 2.1 Create new .env file from default
    DEFAULT_ENV="./default.env"
    NGINX_CONF_TEMPLATE=./nginx/templates/

    cp "$DEFAULT_ENV" "$ENV_FILE"
    echo "" >> "$ENV_FILE"
    echo "SETUP_INCOMPLETE=yes" >> "$ENV_FILE"
    ENV_FILE_CREATED=true
    print_info "Project configuration started"
    echo ""

    # 2.2 Create DJANGO_SECRET_KEY
    DJANGO_SECRET_KEY=$(cat /dev/urandom | tr -dc 'abcdefghijklmnopqrstuvwxyz0123456789!@%^*()_=+' | head -c 50)
    sed -i "s|^#\?\s*DJANGO_SECRET_KEY=.*|DJANGO_SECRET_KEY=$DJANGO_SECRET_KEY|"                  "$ENV_FILE"

    # 2.3 Prompt server address
    DOMAIN_PATTERN='^([a-zA-Z0-9][a-zA-Z0-9-]*\.)+[a-zA-Z]{2,}$'
    IP_PATTERN='^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'

    while true; do
        read -rp "Enter server address (IP, domain or localhost): " SERVER_ADDRESS
        SERVER_ADDRESS=$(strip_invisible "$SERVER_ADDRESS")
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

    # 2.3.2 Set address type boolean flags
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

    # 2.4 Sharable kickoff forms domain
    FORM_DOMAIN=""
    if [ "$ADDRESS_IS_DOMAIN" = true ]; then
        echo ""
        read -rp "Use default address for Sharable kickoff forms ($SERVER_ADDRESS/forms)? [y/n]: " forms_choice
        forms_choice=$(strip_invisible "$forms_choice")
        case "$forms_choice" in
            [Nn]|[Nn][Oo])
                # 2.4.1 Prompt for a separate kickoff forms domain
                while true; do
                    read -rp "Enter domain for Sharable kickoff forms (e.g. forms.example.com): " FORM_DOMAIN
                    FORM_DOMAIN=$(strip_invisible "$FORM_DOMAIN")
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

    # 2.5 Passwords
    if [ "$ADDRESS_IS_LOCALHOST" = false ]; then

        # 2.5.1 Generate passwords (not needed for localhost)
        POSTGRES_PASSWORD=$(gen_password)
        REDIS_PASSWORD=$(gen_password)
        RABBITMQ_PASSWORD=$(gen_password)
        SEAWEEDFS_ACCESS_KEY=$(gen_password 24 20)
        SEAWEEDFS_SECRET_KEY=$(gen_password 48 40)
        FILE_POSTGRES_PASSWORD=$(gen_password)

        # 2.5.2 Write passwords to .env
        sed -i "s|^#\?\s*POSTGRES_PASSWORD=.*|POSTGRES_PASSWORD=$POSTGRES_PASSWORD|"                  "$ENV_FILE"
        sed -i "s|^#\?\s*POSTGRES_REPLICA_PASSWORD=.*|POSTGRES_REPLICA_PASSWORD=$POSTGRES_PASSWORD|"  "$ENV_FILE"
        sed -i "s|^#\?\s*REDIS_PASSWORD=.*|REDIS_PASSWORD=$REDIS_PASSWORD|"                           "$ENV_FILE"
        sed -i "s|^#\?\s*RABBITMQ_PASSWORD=.*|RABBITMQ_PASSWORD=$RABBITMQ_PASSWORD|"                  "$ENV_FILE"
        sed -i "s|^#\?\s*FILE_SEAWEEDFS_S3_ACCESS_KEY=.*|FILE_SEAWEEDFS_S3_ACCESS_KEY=$SEAWEEDFS_ACCESS_KEY|" "$ENV_FILE"
        sed -i "s|^#\?\s*FILE_SEAWEEDFS_S3_SECRET_KEY=.*|FILE_SEAWEEDFS_S3_SECRET_KEY=$SEAWEEDFS_SECRET_KEY|" "$ENV_FILE"
        sed -i "s|^#\?\s*FILE_POSTGRES_PASSWORD=.*|FILE_POSTGRES_PASSWORD=$FILE_POSTGRES_PASSWORD|"   "$ENV_FILE"

    fi

    # 2.6 SSL
    SSL=false
    CERTBOT_ENABLE=false

    # 2.6.1 Prompt to enable SSL if SERVER_ADDRESS is a domain
    if [ "$ADDRESS_IS_DOMAIN" = true ]; then
        echo ""
        while true; do
            read -rp "Enable SSL for $SERVER_ADDRESS? A free Let's Encrypt certificate will be used [y/n]: " ssl_choice
            ssl_choice=$(strip_invisible "$ssl_choice")
            case "$ssl_choice" in
                [Yy]|[Yy][Ee][Ss]) SSL=true;  CERTBOT_ENABLE=true;  break ;;
                [Nn]|[Nn][Oo])     SSL=false; CERTBOT_ENABLE=false; break ;;
                *) print_error "Please answer yes (y) or no (n)." ;;
            esac
        done
        [ "$SSL" = true ] && print_info "SSL enabled"

        # 2.6.2 Write SSL to .env
        _ssl_value="no"
        [ "$SSL" = true ] && _ssl_value="yes"
        sed -i "s|^#\?\s*SSL=.*|SSL=$_ssl_value|" "$ENV_FILE"

        # 2.6.3 Write $CERTBOT_ENABLE to .env
        _certbot_enable_value="no"
        [ "$CERTBOT_ENABLE" = true ] && _certbot_enable_value="yes"
        sed -i "s|^#\?\s*CERTBOT_ENABLE=.*|CERTBOT_ENABLE=$_certbot_enable_value|" "$ENV_FILE"

    fi

    # 2.7 Prompt for CERTBOT_EMAIL if SSL is enabled
    if [ "$CERTBOT_ENABLE" = true ]; then
        EMAIL_PATTERN='^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$'
        echo ""
        while true; do
            read -rp "Enter email for registration free Let's Encrypt SSL certificate: " CERTBOT_EMAIL
            CERTBOT_EMAIL=$(strip_invisible "$CERTBOT_EMAIL")
            if [[ "$CERTBOT_EMAIL" =~ $EMAIL_PATTERN ]]; then
                break
            else
                print_error "Invalid email address. Please try again."
            fi
        done
        print_info "Let's Encrypt certificate will be registered to: $CERTBOT_EMAIL"

        # 2.7.1  Write $CERTBOT_EMAIL to .env
        sed -i "s|^#\?\s*CERTBOT_EMAIL=.*|CERTBOT_EMAIL=$CERTBOT_EMAIL|" "$ENV_FILE"
    fi

    # 2.8 Set Nginx conf template
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

    # 2.9 Set protocol variables
    HTTP_PROTOCOL=http
    WS_PROTOCOL=ws
    [ "$CERTBOT_ENABLE" = true ] && HTTP_PROTOCOL=https
    [ "$CERTBOT_ENABLE" = true ] && WS_PROTOCOL=wss

    # 2.10 Write addresses and URLs to .env
    sed -i "s|^#\?\s*SERVER_ADDRESS=.*|SERVER_ADDRESS=$SERVER_ADDRESS|"                   "$ENV_FILE"
    sed -i "s|^#\?\s*BACKEND_URL=.*|BACKEND_URL=$HTTP_PROTOCOL://$SERVER_ADDRESS:8001|"   "$ENV_FILE"
    sed -i "s|^#\?\s*FRONTEND_URL=.*|FRONTEND_URL=$HTTP_PROTOCOL://$SERVER_ADDRESS|"      "$ENV_FILE"
    sed -i "s|^#\?\s*WSS_URL=.*|WSS_URL=$WS_PROTOCOL://$SERVER_ADDRESS:8001|"             "$ENV_FILE"

    # 2.11 Write forms url to .env
    if [ -n "$FORM_DOMAIN" ]; then
        FORMS_URL="$HTTP_PROTOCOL://$FORM_DOMAIN"
    else
        FORMS_URL="$HTTP_PROTOCOL://$SERVER_ADDRESS/forms"
    fi
    sed -i "s|^#\?\s*FORMS_URL=.*|FORMS_URL=$FORMS_URL|"  "$ENV_FILE"

    # 2.11.1 Write file service URLs to .env
    sed -i "s|^#\?\s*FILE_SERVICE_URL=.*|FILE_SERVICE_URL=$HTTP_PROTOCOL://$SERVER_ADDRESS/files|"     "$ENV_FILE"
    sed -i "s|^#\?\s*FILE_FASTAPI_BASE_URL=.*|FILE_FASTAPI_BASE_URL=$HTTP_PROTOCOL://$SERVER_ADDRESS/files|" "$ENV_FILE"

    # 2.12 Mark setup as complete
    sed -i "/^SETUP_INCOMPLETE=/d" "$ENV_FILE"

fi

# =============================================================================
# 3. Start Docker containers
# =============================================================================

# 3.1.0 Optional modules: compose profiles are derived from LOGS_ENABLE,
# LOGS_BACKEND and MCP_ENABLE and written to COMPOSE_PROFILES of .env,
# so `docker compose up` needs no --profile flags.
_docker_profiles=()
_profiles_changed=false

# 3.1.1 Logging dialog (yes = enabled, no = declined, empty = not decided yet)
_logs_enable=$(read_env_value LOGS_ENABLE)
_logs_backend=$(read_env_value LOGS_BACKEND)
_logs_updates=()

if [ -z "$_logs_enable" ] && [ -n "$_logs_backend" ]; then
    # Installation configured before LOGS_ENABLE existed
    _logs_enable=yes
    _logs_updates+=("LOGS_ENABLE=yes")
    _profiles_changed=true
elif [ -z "$_logs_enable" ]; then
    _profiles_changed=true
    echo ""
    if ask_yes_no "Enable the audit journal (logging)? You will need to enter the receiver's details."; then
        _logs_enable=yes
        echo "Select the receiver backend:"
        echo "  1. OTLP"
        echo "  2. Elasticsearch"
        while true; do
            prompt_value _logs_backend_choice "Enter number (1-2): "
            case "$_logs_backend_choice" in
                1) _logs_backend=otlp;          break ;;
                2) _logs_backend=elasticsearch; break ;;
                *) print_error "Please enter 1 or 2." ;;
            esac
        done

        if [ "$_logs_backend" = otlp ]; then
            prompt_value _logs_otlp_endpoint "Enter the OTLP/HTTP receiver URL: "
            prompt_value _logs_otlp_auth "Enter the authorization header value, e.g. \"Bearer <token>\". Leave empty if the receiver has no authentication (Loki of logging/grafana): "
            _logs_updates+=(
                "LOGS_ENABLE=yes"
                "LOGS_BACKEND=otlp"
                "LOGS_OTLP_EXPORT_ENDPOINT=$_logs_otlp_endpoint"
                "LOGS_OTLP_EXPORT_AUTH=$_logs_otlp_auth"
            )

            print_warning "Logging: OTLP mode. Only the OpenTelemetry collector runs on this machine."
            print_warning "Until the receiver is reachable, events wait in the Redis buffer; once it is full"
            print_warning "the oldest events are dropped. See logging/README.md"
        else
            print_warning "Elasticsearch mode needs the store address (LOGS_ELASTICSEARCH_URL) and collector"
            print_warning "credentials: an API key (LOGS_ELASTICSEARCH_API_KEY) or a login and password."
            while true; do
                prompt_value _logs_es_url "Enter the Elasticsearch URL (LOGS_ELASTICSEARCH_URL, e.g. https://es.example.internal:9200): "
                [[ "$_logs_es_url" =~ ^https:// ]] && break
                print_error "The URL must start with https://"
            done

            echo "Select how the collector authenticates (set one pair, never both):"
            echo "  1. API key (recommended)"
            echo "  2. Login and password"
            while true; do
                prompt_value _logs_es_auth_choice "Enter number (1-2): "
                case "$_logs_es_auth_choice" in
                    1|2) break ;;
                    *) print_error "Please enter 1 or 2." ;;
                esac
            done

            _logs_es_api_key=""
            _logs_es_user=""
            _logs_es_password=""
            if [ "$_logs_es_auth_choice" = 1 ]; then
                while [ -z "$_logs_es_api_key" ]; do
                    prompt_value _logs_es_api_key "Enter the API key (LOGS_ELASTICSEARCH_API_KEY): "
                    [ -n "$_logs_es_api_key" ] || print_error "The API key cannot be empty."
                done
            else
                while [ -z "$_logs_es_user" ]; do
                    prompt_value _logs_es_user "Enter the login (LOGS_ELASTICSEARCH_USER): "
                    [ -n "$_logs_es_user" ] || print_error "The login cannot be empty."
                done
                while [ -z "$_logs_es_password" ]; do
                    prompt_value _logs_es_password "Enter the password (LOGS_ELASTICSEARCH_PASSWORD): "
                    [ -n "$_logs_es_password" ] || print_error "The password cannot be empty."
                done
            fi

            _logs_updates+=(
                "LOGS_ENABLE=yes"
                "LOGS_BACKEND=elasticsearch"
                "LOGS_ELASTICSEARCH_URL=$_logs_es_url"
                "LOGS_ELASTICSEARCH_API_KEY=$_logs_es_api_key"
                "LOGS_ELASTICSEARCH_USER=$_logs_es_user"
                "LOGS_ELASTICSEARCH_PASSWORD=$_logs_es_password"
            )

            print_info "Logging: Elasticsearch mode. Only the OpenTelemetry collector runs on this machine."
            print_info "Elasticsearch and Kibana must run on a separate storage server (logging/elasticsearch)."
            print_info "Undelivered batches are kept on disk in ./otel-queue and survive collector restarts."
            print_warning "The collector connects to Elasticsearch over HTTPS and must trust its certificate."
            print_warning "Copy logging/elasticsearch/certs/ca/ca.crt from the storage server to otel-collector/es-ca.crt"
            print_warning "on this machine. For a publicly trusted certificate, set LOGS_ELASTICSEARCH_CA_FILE= (empty)."
            print_info "Details: logging/README.md, section \"Elasticsearch + Kibana\""
        fi
    else
        _logs_enable=no
        _logs_backend=""
        _logs_updates+=("LOGS_ENABLE=no" "LOGS_BACKEND=")
    fi
fi

# 3.1.2 Logging profiles
if [ "$_logs_enable" = yes ]; then
    _docker_profiles+=("logs-$_logs_backend")
fi

# 3.1.3 Write logging values
if [ ${#_logs_updates[@]} -gt 0 ]; then
    write_env_vars "${_logs_updates[@]}"
fi

# 3.1.4 MCP dialog
_mcp_enable=$(read_env_value MCP_ENABLE)
_mcp_updates=()

if [ -z "$_mcp_enable" ]; then
    _profiles_changed=true
    echo ""
    if ask_yes_no "Enable the MCP connector?"; then
        _mcp_enable=yes
    else
        _mcp_enable=no
    fi
    _mcp_updates+=("MCP_ENABLE=$_mcp_enable")
fi

if [ "$_mcp_enable" = yes ]; then
    if [ -z "$(read_env_value MCP_SECRET)" ]; then
        _mcp_updates+=("MCP_SECRET=$(openssl rand -hex 32)")
    fi
    MCP_PUBLIC_ORIGIN=$(read_env_value MCP_PUBLIC_URL)
    if [ -z "$MCP_PUBLIC_ORIGIN" ]; then
        MCP_PUBLIC_ORIGIN=$(read_env_value FRONTEND_URL)
    fi
    case "$MCP_PUBLIC_ORIGIN" in
      https://*|http://localhost|http://localhost:*|http://127.0.0.1|http://127.0.0.1:*|"")
        ;;
      *)
        print_warning "The MCP server needs HTTPS outside localhost (PUBLIC_URL=$MCP_PUBLIC_ORIGIN): set MCP_PUBLIC_URL or FRONTEND_URL to an https:// origin"
        ;;
    esac
fi

# 3.1.5 MCP profiles
if [ "$_mcp_enable" = yes ]; then
    _docker_profiles+=("mcp")
fi

# 3.1.6 Write MCP values and COMPOSE_PROFILES
if [ "$_profiles_changed" = true ]; then
    _mcp_updates+=("COMPOSE_PROFILES=$(IFS=,; echo "${_docker_profiles[*]}")")
fi
if [ ${#_mcp_updates[@]} -gt 0 ]; then
    write_env_vars "${_mcp_updates[@]}"
fi

# 3.1.7 Prepare the collector queue directory (owned by the uid of the collector image)
if [ "$_logs_enable" = yes ] && [ "$_logs_backend" = elasticsearch ]; then
    mkdir -p ./otel-queue
    if ! output=$(docker run --rm -v "$SCRIPT_DIR/otel-queue:/q" alpine chown 10001:10001 /q 2>&1); then
        print_error "$output"
        exit 1
    fi
fi

# 2.9 Write SeaweedFS S3 config (only on first setup, same guard as passwords)
# We generate this file directly because seaweedfs-filer does not natively support env variables for S3 credentials
if [ "$ENV_FILE_CREATED" = true ]; then
    S3_AK=$(grep '^FILE_SEAWEEDFS_S3_ACCESS_KEY=' "$ENV_FILE" | cut -d '=' -f2)
    S3_SK=$(grep '^FILE_SEAWEEDFS_S3_SECRET_KEY=' "$ENV_FILE" | cut -d '=' -f2)

    cat <<EOF > ./storage/seaweedfs/s3.json
{
  "identities": [
    {
      "name": "file-service",
      "credentials": [
        {
          "accessKey": "${S3_AK:-any-secret-key-will-work}",
          "secretKey": "${S3_SK:-any-secret-key-will-work}"
        }
      ],
      "actions": [
        "Read",
        "Write",
        "List",
        "Tagging",
        "Admin"
      ]
    }
  ]
}
EOF
fi

# 3.1 Select docker-compose configuration
echo ""
echo "Select a version to start:"
echo "  1. Stable (recommended)"
echo "  2. Latest"
echo "  3. From sources (Branch: \"$GIT_BRANCH\")"

while true; do
    read -r -p "Enter number (1-3): " COMPOSE_FILE
    COMPOSE_FILE=$(strip_invisible "$COMPOSE_FILE")

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

# 3.2 Start containers

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
# 4. Summary
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
