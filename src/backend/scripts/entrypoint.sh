#!/bin/bash

# Production entrypoint script for Transfer Requirements Management System
# Version: 1.0.0
# Dependencies: Python 3.11+, Django 4.2+, PostgreSQL 14+

# Exit on error, undefined variables, and pipe failures
set -euo pipefail

# Script constants
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly LOCK_FILE="/tmp/django_startup.lock"
readonly LOG_DIR="/var/log/django"
readonly LOG_FILE="${LOG_DIR}/entrypoint.log"
readonly MAX_RETRIES=3
readonly RETRY_DELAY=5

# Source required scripts
source "${SCRIPT_DIR}/migrate.sh"
source "${SCRIPT_DIR}/collect-static.sh"
source "${SCRIPT_DIR}/start-prod.sh"

# Initialize logging with JSON format
setup_logging() {
    mkdir -p "${LOG_DIR}"
    exec 1> >(tee -a "${LOG_FILE}")
    exec 2> >(tee -a "${LOG_FILE}")
    
    echo "{\"timestamp\":\"$(date -u +"%Y-%m-%dT%H:%M:%SZ")\",\"level\":\"INFO\",\"message\":\"Starting application initialization\"}"
}

# Cleanup function for error handling
cleanup() {
    local exit_code=$?
    echo "{\"timestamp\":\"$(date -u +"%Y-%m-%dT%H:%M:%SZ")\",\"level\":\"INFO\",\"message\":\"Cleaning up resources\"}"
    
    # Remove lock file if it exists
    [ -f "${LOCK_FILE}" ] && rm "${LOCK_FILE}"
    
    # Stop any running processes
    pkill -P $$ || true
    
    # Log exit status
    if [ $exit_code -ne 0 ]; then
        echo "{\"timestamp\":\"$(date -u +"%Y-%m-%dT%H:%M:%SZ")\",\"level\":\"ERROR\",\"message\":\"Application failed to start\",\"exit_code\":$exit_code}"
    fi
    
    exit $exit_code
}

# Set up error handling
trap cleanup EXIT ERR TERM INT HUP

# Check environment and dependencies
check_environment() {
    local required_vars=(
        "DJANGO_SETTINGS_MODULE"
        "DJANGO_SECRET_KEY"
        "ALLOWED_HOSTS"
        "DATABASE_URL"
        "REDIS_URL"
        "AWS_ACCESS_KEY_ID"
        "AWS_SECRET_ACCESS_KEY"
        "AWS_STORAGE_BUCKET_NAME"
    )

    # Verify required environment variables
    for var in "${required_vars[@]}"; do
        if [ -z "${!var:-}" ]; then
            echo "{\"timestamp\":\"$(date -u +"%Y-%m-%dT%H:%M:%SZ")\",\"level\":\"ERROR\",\"message\":\"Missing required environment variable\",\"variable\":\"$var\"}"
            return 1
        fi
    done

    # Check Python version
    if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 11) else 1)"; then
        echo "{\"timestamp\":\"$(date -u +"%Y-%m-%dT%H:%M:%SZ")\",\"level\":\"ERROR\",\"message\":\"Python 3.11+ is required\"}"
        return 1
    fi

    # Verify database connection
    if ! python3 -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', '${DJANGO_SETTINGS_MODULE}')
django.setup()
from django.db import connections
connections['default'].ensure_connection()
"; then
        echo "{\"timestamp\":\"$(date -u +"%Y-%m-%dT%H:%M:%SZ")\",\"level\":\"ERROR\",\"message\":\"Database connection failed\"}"
        return 1
    fi

    # Check Redis connection
    if ! python3 -c "
import os, django, redis
os.environ.setdefault('DJANGO_SETTINGS_MODULE', '${DJANGO_SETTINGS_MODULE}')
django.setup()
from django.conf import settings
redis.from_url(settings.CACHES['default']['LOCATION']).ping()
"; then
        echo "{\"timestamp\":\"$(date -u +"%Y-%m-%dT%H:%M:%SZ")\",\"level\":\"ERROR\",\"message\":\"Redis connection failed\"}"
        return 1
    fi

    return 0
}

# Initialize application components
initialize_application() {
    echo "{\"timestamp\":\"$(date -u +"%Y-%m-%dT%H:%M:%SZ")\",\"level\":\"INFO\",\"message\":\"Initializing application components\"}"
    
    # Create initialization lock
    if ! touch "${LOCK_FILE}"; then
        echo "{\"timestamp\":\"$(date -u +"%Y-%m-%dT%H:%M:%SZ")\",\"level\":\"ERROR\",\"message\":\"Unable to create lock file\"}"
        return 1
    fi
    
    # Run database migrations
    if ! run_migrations; then
        echo "{\"timestamp\":\"$(date -u +"%Y-%m-%dT%H:%M:%SZ")\",\"level\":\"ERROR\",\"message\":\"Database migration failed\"}"
        return 1
    fi
    
    # Collect static files
    if ! collect_static; then
        echo "{\"timestamp\":\"$(date -u +"%Y-%m-%dT%H:%M:%SZ")\",\"level\":\"ERROR\",\"message\":\"Static file collection failed\"}"
        return 1
    fi
    
    # Run Django system checks
    if ! python3 manage.py check --deploy; then
        echo "{\"timestamp\":\"$(date -u +"%Y-%m-%dT%H:%M:%SZ")\",\"level\":\"ERROR\",\"message\":\"Django system checks failed\"}"
        return 1
    fi
    
    return 0
}

# Start application with health checks
start_application() {
    echo "{\"timestamp\":\"$(date -u +"%Y-%m-%dT%H:%M:%SZ")\",\"level\":\"INFO\",\"message\":\"Starting application\"}"
    
    # Calculate optimal number of workers
    export WORKERS=$((2 * $(nproc) + 1))
    export MAX_REQUESTS=1000
    export MAX_REQUESTS_JITTER=50
    export GRACEFUL_TIMEOUT=30
    export TIMEOUT=60
    
    # Start Gunicorn with production settings
    exec gunicorn config.wsgi:application \
        --name transfer_requirements \
        --workers ${WORKERS} \
        --worker-class gevent \
        --worker-tmp-dir /dev/shm \
        --bind 0.0.0.0:${APP_PORT:-8000} \
        --max-requests ${MAX_REQUESTS} \
        --max-requests-jitter ${MAX_REQUESTS_JITTER} \
        --graceful-timeout ${GRACEFUL_TIMEOUT} \
        --timeout ${TIMEOUT} \
        --keep-alive 5 \
        --log-level ${LOG_LEVEL:-INFO} \
        --access-logfile ${LOG_DIR}/gunicorn-access.log \
        --error-logfile ${LOG_DIR}/gunicorn-error.log \
        --capture-output \
        --enable-stdio-inheritance \
        --preload
}

# Main execution
main() {
    setup_logging
    
    echo "{\"timestamp\":\"$(date -u +"%Y-%m-%dT%H:%M:%SZ")\",\"level\":\"INFO\",\"message\":\"Starting Transfer Requirements Management System\"}"
    
    # Check environment
    if ! check_environment; then
        echo "{\"timestamp\":\"$(date -u +"%Y-%m-%dT%H:%M:%SZ")\",\"level\":\"ERROR\",\"message\":\"Environment check failed\"}"
        exit 1
    fi
    
    # Initialize application
    if ! initialize_application; then
        echo "{\"timestamp\":\"$(date -u +"%Y-%m-%dT%H:%M:%SZ")\",\"level\":\"ERROR\",\"message\":\"Application initialization failed\"}"
        exit 1
    fi
    
    # Start application
    start_application
}

# Execute main function
main "$@"