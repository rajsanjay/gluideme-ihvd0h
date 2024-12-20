#!/bin/bash

# Production startup script for Transfer Requirements Management System
# Version: 1.0.0
# Requires: Python 3.11+, Gunicorn 20.1+

set -e  # Exit on error
set -u  # Exit on undefined variables

# Environment configuration
export DJANGO_SETTINGS_MODULE="config.settings.production"
export PYTHONPATH="/app/backend:${PYTHONPATH:-}"
export PROMETHEUS_MULTIPROC_DIR="/tmp/prometheus_multiproc"

# Gunicorn settings - Dynamic worker calculation based on CPU cores
# Using recommended formula: 2 * num_cores + 1
export GUNICORN_WORKERS="$(( 2 * $(nproc) + 1 ))"
export GUNICORN_THREADS="4"
export GUNICORN_TIMEOUT="120"
export GUNICORN_MAX_REQUESTS="1000"
export GUNICORN_MAX_REQUESTS_JITTER="50"
export GUNICORN_GRACEFUL_TIMEOUT="30"
export GUNICORN_KEEPALIVE="5"

# Function to check required environment variables and system prerequisites
check_environment() {
    local required_vars=(
        "DJANGO_SECRET_KEY"
        "ALLOWED_HOSTS"
        "DB_NAME"
        "DB_USER"
        "DB_PASSWORD"
        "DB_HOST"
        "REDIS_URL"
        "AWS_ACCESS_KEY_ID"
        "AWS_SECRET_ACCESS_KEY"
        "AWS_STORAGE_BUCKET_NAME"
    )

    for var in "${required_vars[@]}"; do
        if [[ -z "${!var:-}" ]]; then
            echo "ERROR: Required environment variable $var is not set"
            return 1
        fi
    done

    # Check Python version
    if ! command -v python3.11 &> /dev/null; then
        echo "ERROR: Python 3.11+ is required"
        return 1
    fi

    # Check disk space (minimum 1GB free)
    if [[ $(df -m / | awk 'NR==2 {print $4}') -lt 1024 ]]; then
        echo "ERROR: Insufficient disk space"
        return 1
    }

    return 0
}

# Function to setup logging configuration
setup_logging() {
    local log_dir="/var/log/django"
    
    # Create log directory if it doesn't exist
    mkdir -p "${log_dir}"
    chmod 755 "${log_dir}"

    # Create prometheus multiprocess directory
    mkdir -p "${PROMETHEUS_MULTIPROC_DIR}"
    chmod 777 "${PROMETHEUS_MULTIPROC_DIR}"

    # Setup log rotation
    cat > /etc/logrotate.d/django << EOF
${log_dir}/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0644 www-data www-data
    sharedscripts
    postrotate
        systemctl reload gunicorn.service
    endscript
}
EOF
}

# Function to start Gunicorn with production settings
start_gunicorn() {
    echo "Starting Gunicorn with ${GUNICORN_WORKERS} workers..."
    
    exec gunicorn config.wsgi:application \
        --name transfer_requirements \
        --workers "${GUNICORN_WORKERS}" \
        --threads "${GUNICORN_THREADS}" \
        --worker-class gevent \
        --worker-tmp-dir /dev/shm \
        --timeout "${GUNICORN_TIMEOUT}" \
        --graceful-timeout "${GUNICORN_GRACEFUL_TIMEOUT}" \
        --keep-alive "${GUNICORN_KEEPALIVE}" \
        --max-requests "${GUNICORN_MAX_REQUESTS}" \
        --max-requests-jitter "${GUNICORN_MAX_REQUESTS_JITTER}" \
        --bind 0.0.0.0:8000 \
        --log-level info \
        --error-logfile /var/log/django/gunicorn-error.log \
        --access-logfile /var/log/django/gunicorn-access.log \
        --capture-output \
        --enable-stdio-inheritance \
        --preload \
        --statsd-host localhost:9125 \
        --statsd-prefix transfer_requirements \
        --config python:config.gunicorn_conf
}

# Main execution
main() {
    echo "Starting Transfer Requirements Management System in production mode..."

    # Perform environment checks
    if ! check_environment; then
        echo "Environment check failed. Exiting."
        exit 1
    fi

    # Setup logging
    setup_logging

    # Change to application directory
    cd /app/backend

    # Run database migrations
    echo "Running database migrations..."
    python manage.py migrate --noinput

    # Collect static files
    echo "Collecting static files..."
    python manage.py collectstatic --noinput

    # Start Gunicorn
    start_gunicorn
}

# Execute main function
main "$@"