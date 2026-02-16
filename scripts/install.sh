#!/bin/bash
#
# Petrix - Installation Script
# One-liner: curl -fsSL https://get.petrix.io | bash
#
# This script installs Petrix on a fresh server.
# Tested on: Ubuntu 22.04, Debian 12, RHEL 9, Rocky 9
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PETRIX_VERSION="${PETRIX_VERSION:-latest}"
PETRIX_INSTALL_DIR="${PETRIX_INSTALL_DIR:-/opt/petrix}"
PETRIX_DATA_DIR="${PETRIX_DATA_DIR:-/var/lib/petrix}"
PETRIX_DOMAIN="${PETRIX_DOMAIN:-localhost}"

# Functions
print_banner() {
    echo -e "${BLUE}"
    echo "  _____     _        _        "
    echo " |  __ \   | |      (_)       "
    echo " | |__) ___| |_ _ __ ___  __ "
    echo " |  ___/ _ \ __| '__| \ \/ / "
    echo " | |  |  __/ |_| |  | |>  <  "
    echo " |_|   \___|\__|_|  |_/_/\_\ "
    echo -e "${NC}"
    echo ""
    echo "Petrix Installer v${PETRIX_VERSION}"
    echo "==========================================="
    echo ""
}

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "This script must be run as root (use sudo)"
        exit 1
    fi
}

check_os() {
    if [[ -f /etc/os-release ]]; then
        . /etc/os-release
        OS=$ID
        VERSION=$VERSION_ID
        log_info "Detected OS: $PRETTY_NAME"
    else
        log_error "Cannot detect OS. /etc/os-release not found."
        exit 1
    fi

    case $OS in
        ubuntu|debian|rhel|rocky|centos|fedora|almalinux)
            log_info "OS is supported"
            ;;
        *)
            log_warn "OS '$OS' is not officially supported. Proceeding anyway..."
            ;;
    esac
}

check_requirements() {
    log_info "Checking system requirements..."

    # Check RAM (minimum 2GB)
    TOTAL_RAM=$(free -m | awk '/^Mem:/{print $2}')
    if [[ $TOTAL_RAM -lt 1900 ]]; then
        log_warn "Less than 2GB RAM detected ($TOTAL_RAM MB). Performance may be affected."
    else
        log_info "RAM: ${TOTAL_RAM}MB (OK)"
    fi

    # Check disk space (minimum 10GB)
    AVAILABLE_SPACE=$(df -BG / | awk 'NR==2 {print $4}' | tr -d 'G')
    if [[ $AVAILABLE_SPACE -lt 10 ]]; then
        log_error "Less than 10GB disk space available. Please free up space."
        exit 1
    else
        log_info "Disk: ${AVAILABLE_SPACE}GB available (OK)"
    fi
}

install_docker() {
    if command -v docker &> /dev/null; then
        log_info "Docker is already installed"
        docker --version
    else
        log_info "Installing Docker..."

        case $OS in
            ubuntu|debian)
                apt-get update
                apt-get install -y ca-certificates curl gnupg
                install -m 0755 -d /etc/apt/keyrings
                curl -fsSL https://download.docker.com/linux/$OS/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
                chmod a+r /etc/apt/keyrings/docker.gpg
                echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/$OS $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
                apt-get update
                apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
                ;;
            rhel|centos|rocky|almalinux|fedora)
                dnf install -y dnf-plugins-core
                dnf config-manager --add-repo https://download.docker.com/linux/rhel/docker-ce.repo
                dnf install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
                ;;
            *)
                log_error "Cannot install Docker automatically on $OS"
                exit 1
                ;;
        esac

        systemctl enable docker
        systemctl start docker
        log_info "Docker installed successfully"
    fi
}

generate_secrets() {
    log_info "Generating secure secrets..."

    SECRET_KEY=$(openssl rand -hex 32)
    POSTGRES_PASSWORD=$(openssl rand -hex 16)
    ADMIN_PASSWORD=$(openssl rand -base64 16 | tr -d '/+=')

    # Ensure admin password meets requirements
    ADMIN_PASSWORD="${ADMIN_PASSWORD}Aa1!"
}

create_directories() {
    log_info "Creating directories..."

    mkdir -p "$PETRIX_INSTALL_DIR"
    mkdir -p "$PETRIX_DATA_DIR/postgres"
    mkdir -p "$PETRIX_DATA_DIR/redis"
    mkdir -p "$PETRIX_DATA_DIR/backups"

    chmod 700 "$PETRIX_DATA_DIR"
}

download_platform() {
    log_info "Downloading Petrix..."

    cd "$PETRIX_INSTALL_DIR"

    # In production, this would download from your release server
    # For now, we create the necessary files

    # Create docker-compose.yml for production
    cat > docker-compose.yml << 'COMPOSE_EOF'
services:
  db:
    image: postgres:16-alpine
    container_name: petrix-db
    restart: unless-stopped
    environment:
      POSTGRES_USER: petrix
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: petrix
    volumes:
      - ${PETRIX_DATA_DIR}/postgres:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U petrix"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: petrix-redis
    restart: unless-stopped
    volumes:
      - ${PETRIX_DATA_DIR}/redis:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    image: ghcr.io/your-org/petrix-backend:${PETRIX_VERSION:-latest}
    container_name: petrix-backend
    restart: unless-stopped
    environment:
      - DATABASE_URL=postgresql://petrix:${POSTGRES_PASSWORD}@db:5432/petrix
      - REDIS_URL=redis://redis:6379/0
      - SECRET_KEY=${SECRET_KEY}
      - DEBUG=false
      - CORS_ORIGINS=https://${PETRIX_DOMAIN}
      - ADMIN_EMAIL=${ADMIN_EMAIL:-admin@petrix.local}
      - ADMIN_PASSWORD=${ADMIN_PASSWORD}
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy

  frontend:
    image: ghcr.io/your-org/petrix-frontend:${PETRIX_VERSION:-latest}
    container_name: petrix-frontend
    restart: unless-stopped
    environment:
      - VITE_API_URL=https://${PETRIX_DOMAIN}/api
    depends_on:
      - backend

  nginx:
    image: nginx:alpine
    container_name: petrix-nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
      - ${PETRIX_DATA_DIR}/certbot:/var/www/certbot:ro
    depends_on:
      - backend
      - frontend

  celery:
    image: ghcr.io/your-org/petrix-backend:${PETRIX_VERSION:-latest}
    container_name: petrix-celery
    restart: unless-stopped
    environment:
      - DATABASE_URL=postgresql://petrix:${POSTGRES_PASSWORD}@db:5432/petrix
      - REDIS_URL=redis://redis:6379/0
      - SECRET_KEY=${SECRET_KEY}
    command: celery -A app.workers worker --loglevel=info
    depends_on:
      - backend
      - redis
COMPOSE_EOF

    # Create nginx configuration
    cat > nginx.conf << 'NGINX_EOF'
events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Gzip
    gzip on;
    gzip_types text/plain text/css application/json application/javascript;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;

    upstream backend {
        server backend:8000;
    }

    upstream frontend {
        server frontend:5173;
    }

    server {
        listen 80;
        server_name _;

        # Let's Encrypt challenge
        location /.well-known/acme-challenge/ {
            root /var/www/certbot;
        }

        # Redirect to HTTPS (uncomment in production with SSL)
        # return 301 https://$host$request_uri;

        # For testing without SSL
        location /api {
            limit_req zone=api burst=20 nodelay;
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        location / {
            proxy_pass http://frontend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
        }
    }

    # HTTPS server (uncomment and configure with real SSL certs)
    # server {
    #     listen 443 ssl http2;
    #     server_name _;
    #
    #     ssl_certificate /etc/nginx/ssl/fullchain.pem;
    #     ssl_certificate_key /etc/nginx/ssl/privkey.pem;
    #     ssl_protocols TLSv1.2 TLSv1.3;
    #     ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
    #     ssl_prefer_server_ciphers off;
    #
    #     location /api {
    #         limit_req zone=api burst=20 nodelay;
    #         proxy_pass http://backend;
    #         proxy_set_header Host $host;
    #         proxy_set_header X-Real-IP $remote_addr;
    #         proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    #         proxy_set_header X-Forwarded-Proto $scheme;
    #     }
    #
    #     location / {
    #         proxy_pass http://frontend;
    #         proxy_set_header Host $host;
    #         proxy_set_header X-Real-IP $remote_addr;
    #     }
    # }
}
NGINX_EOF

    mkdir -p ssl
}

create_env_file() {
    log_info "Creating environment file..."

    cat > "$PETRIX_INSTALL_DIR/.env" << ENV_EOF
# Petrix Configuration
# Generated on $(date)

# Version
PETRIX_VERSION=${PETRIX_VERSION}

# Domain (change this to your domain)
PETRIX_DOMAIN=${PETRIX_DOMAIN}

# Data directory
PETRIX_DATA_DIR=${PETRIX_DATA_DIR}

# Security (auto-generated, do not share)
SECRET_KEY=${SECRET_KEY}
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}

# Admin credentials
ADMIN_EMAIL=admin@${PETRIX_DOMAIN}
ADMIN_PASSWORD=${ADMIN_PASSWORD}
ENV_EOF

    chmod 600 "$PETRIX_INSTALL_DIR/.env"
}

create_management_script() {
    log_info "Creating management script..."

    cat > /usr/local/bin/petrix << 'SCRIPT_EOF'
#!/bin/bash
#
# Petrix Management Script
#

PETRIX_DIR="/opt/petrix"
cd "$PETRIX_DIR" || exit 1

case "$1" in
    start)
        echo "Starting Petrix..."
        docker compose up -d
        ;;
    stop)
        echo "Stopping Petrix..."
        docker compose down
        ;;
    restart)
        echo "Restarting Petrix..."
        docker compose restart
        ;;
    status)
        docker compose ps
        ;;
    logs)
        shift
        docker compose logs -f "$@"
        ;;
    update)
        echo "Updating Petrix..."
        docker compose pull
        docker compose up -d
        ;;
    backup)
        BACKUP_FILE="/var/lib/petrix/backups/backup-$(date +%Y%m%d-%H%M%S).sql"
        echo "Creating backup: $BACKUP_FILE"
        docker compose exec -T db pg_dump -U petrix petrix > "$BACKUP_FILE"
        gzip "$BACKUP_FILE"
        echo "Backup created: ${BACKUP_FILE}.gz"
        ;;
    restore)
        if [[ -z "$2" ]]; then
            echo "Usage: petrix restore <backup_file>"
            exit 1
        fi
        echo "Restoring from: $2"
        gunzip -c "$2" | docker compose exec -T db psql -U petrix petrix
        ;;
    shell)
        docker compose exec backend bash
        ;;
    *)
        echo "Petrix Management"
        echo ""
        echo "Usage: petrix <command>"
        echo ""
        echo "Commands:"
        echo "  start    Start all services"
        echo "  stop     Stop all services"
        echo "  restart  Restart all services"
        echo "  status   Show service status"
        echo "  logs     View logs (optionally specify service)"
        echo "  update   Pull latest images and restart"
        echo "  backup   Create database backup"
        echo "  restore  Restore from backup file"
        echo "  shell    Open shell in backend container"
        ;;
esac
SCRIPT_EOF

    chmod +x /usr/local/bin/petrix
}

start_services() {
    log_info "Starting Petrix..."

    cd "$PETRIX_INSTALL_DIR"

    # For initial setup without pre-built images, build locally
    # In production, images would be pulled from registry
    docker compose up -d

    log_info "Waiting for services to be ready..."
    sleep 10

    # Check if services are running
    if docker compose ps | grep -q "Up"; then
        log_info "Services started successfully"
    else
        log_error "Some services failed to start. Check logs with: petrix logs"
    fi
}

print_summary() {
    echo ""
    echo -e "${GREEN}=========================================${NC}"
    echo -e "${GREEN}  Petrix Installation Complete!   ${NC}"
    echo -e "${GREEN}=========================================${NC}"
    echo ""
    echo "Access your Petrix instance:"
    echo "  URL:      http://${PETRIX_DOMAIN}"
    echo "  Email:    admin@${PETRIX_DOMAIN}"
    echo "  Password: ${ADMIN_PASSWORD}"
    echo ""
    echo "Important files:"
    echo "  Config:   ${PETRIX_INSTALL_DIR}/.env"
    echo "  Data:     ${PETRIX_DATA_DIR}"
    echo ""
    echo "Management commands:"
    echo "  petrix start    - Start services"
    echo "  petrix stop     - Stop services"
    echo "  petrix logs     - View logs"
    echo "  petrix backup   - Create backup"
    echo "  petrix update   - Update to latest"
    echo ""
    echo -e "${YELLOW}IMPORTANT: Save your admin password securely!${NC}"
    echo -e "${YELLOW}Change it after first login.${NC}"
    echo ""
}

# Main
main() {
    print_banner
    check_root
    check_os
    check_requirements
    install_docker
    generate_secrets
    create_directories
    download_platform
    create_env_file
    create_management_script
    # start_services  # Commented out - user should start manually after review
    print_summary
}

main "$@"
