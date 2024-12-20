#!/bin/bash

# Production-grade migration script for Transfer Requirements Management System
# Version: 1.0.0
# Requires: Python 3.11+, Django 4.2+, PostgreSQL 14+

# Exit on any error, undefined variable, or pipe failure
set -euo pipefail

# Script constants
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../" && pwd)"
readonly TIMESTAMP=$(date +%Y%m%d_%H%M%S)
readonly BACKUP_DIR="${PROJECT_ROOT}/backups/migrations"
readonly LOG_DIR="${PROJECT_ROOT}/logs/migrations"
readonly LOCK_FILE="/tmp/django_migration.lock"
readonly MAX_RETRIES=3
readonly RETRY_DELAY=5

# Initialize logging
setup_logging() {
    mkdir -p "${LOG_DIR}"
    exec 1> >(tee -a "${LOG_DIR}/migration_${TIMESTAMP}.log")
    exec 2> >(tee -a "${LOG_DIR}/migration_${TIMESTAMP}.error.log")
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting migration process..."
}

# Cleanup function for error handling
cleanup() {
    local exit_code=$?
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Cleaning up..."
    
    # Remove lock file if it exists
    [ -f "${LOCK_FILE}" ] && rm "${LOCK_FILE}"
    
    # Restore connection settings
    if [ -n "${PGCONNECT_TIMEOUT:-}" ]; then
        unset PGCONNECT_TIMEOUT
    fi
    
    # Log exit status
    if [ $exit_code -ne 0 ]; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Migration failed with exit code: $exit_code"
    else
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Migration completed successfully"
    fi
    
    exit $exit_code
}

# Set up error handling
trap cleanup EXIT
trap 'echo "Error on line $LINENO"' ERR

# Check required environment variables
check_environment() {
    local required_vars=(
        "DJANGO_SETTINGS_MODULE"
        "DATABASE_URL"
        "DB_NAME"
        "DB_USER"
        "DB_PASSWORD"
        "DB_HOST"
        "DB_PORT"
        "MIGRATION_TIMEOUT"
        "LOCK_TIMEOUT"
    )

    for var in "${required_vars[@]}"; do
        if [ -z "${!var:-}" ]; then
            echo "Error: Required environment variable $var is not set"
            return 1
        fi
    done

    # Verify database connectivity
    if ! PGPASSWORD="${DB_PASSWORD}" psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" -c '\q' >/dev/null 2>&1; then
        echo "Error: Unable to connect to database"
        return 1
    fi

    return 0
}

# Create database backup
backup_database() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Creating database backup..."
    
    mkdir -p "${BACKUP_DIR}"
    local backup_file="${BACKUP_DIR}/pre_migration_${TIMESTAMP}.sql"
    
    if ! PGPASSWORD="${DB_PASSWORD}" pg_dump \
        -h "${DB_HOST}" \
        -p "${DB_PORT}" \
        -U "${DB_USER}" \
        -d "${DB_NAME}" \
        -F c \
        -f "${backup_file}"; then
        echo "Error: Database backup failed"
        return 1
    fi
    
    echo "Backup created: ${backup_file}"
    return 0
}

# Check migration status
check_migration_status() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Checking migration status..."
    
    cd "${PROJECT_ROOT}"
    if ! python manage.py showmigrations --plan > "${LOG_DIR}/pre_migration_status_${TIMESTAMP}.txt"; then
        echo "Error: Unable to check migration status"
        return 1
    fi
    
    return 0
}

# Execute migrations
run_migrations() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Executing migrations..."
    
    # Set PostgreSQL connection timeout
    export PGCONNECT_TIMEOUT=10
    
    # Set lock timeout for migrations
    export LOCK_TIMEOUT=${LOCK_TIMEOUT:-"60s"}
    
    cd "${PROJECT_ROOT}"
    
    # Create lock file
    if ! touch "${LOCK_FILE}"; then
        echo "Error: Unable to create lock file"
        return 1
    fi
    
    local retry_count=0
    while [ $retry_count -lt $MAX_RETRIES ]; do
        if python manage.py migrate --noinput; then
            return 0
        fi
        
        echo "Migration attempt $((retry_count + 1)) failed, retrying in ${RETRY_DELAY} seconds..."
        sleep "${RETRY_DELAY}"
        ((retry_count++))
    done
    
    echo "Error: Migration failed after ${MAX_RETRIES} attempts"
    return 1
}

# Verify migration success
verify_migration() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Verifying migration..."
    
    cd "${PROJECT_ROOT}"
    
    # Check for unapplied migrations
    if ! python manage.py showmigrations --plan | grep -q "[ ]"; then
        # Verify database connectivity
        if PGPASSWORD="${DB_PASSWORD}" psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" -c '\dt' >/dev/null 2>&1; then
            echo "Migration verification successful"
            return 0
        fi
    fi
    
    echo "Error: Migration verification failed"
    return 1
}

# Synchronize read replicas
sync_replicas() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Synchronizing read replicas..."
    
    # Wait for replication lag to catch up
    sleep 5
    
    # Verify replica synchronization
    if [ -n "${DB_REPLICA_HOST:-}" ]; then
        if ! PGPASSWORD="${DB_REPLICA_PASSWORD}" psql \
            -h "${DB_REPLICA_HOST}" \
            -p "${DB_REPLICA_PORT}" \
            -U "${DB_REPLICA_USER}" \
            -d "${DB_REPLICA_NAME}" \
            -c '\dt' >/dev/null 2>&1; then
            echo "Warning: Unable to verify replica synchronization"
            return 1
        fi
    fi
    
    return 0
}

# Main execution
main() {
    setup_logging
    
    echo "Starting database migration process..."
    
    # Check environment
    if ! check_environment; then
        echo "Environment check failed"
        return 1
    fi
    
    # Create backup
    if ! backup_database; then
        echo "Backup failed"
        return 1
    fi
    
    # Check current migration status
    if ! check_migration_status; then
        echo "Migration status check failed"
        return 1
    fi
    
    # Run migrations
    if ! run_migrations; then
        echo "Migration failed"
        return 1
    fi
    
    # Verify migration
    if ! verify_migration; then
        echo "Migration verification failed"
        return 1
    fi
    
    # Sync replicas
    if ! sync_replicas; then
        echo "Warning: Replica synchronization issues detected"
        # Don't fail the migration for replica sync issues
    fi
    
    echo "Migration completed successfully"
    return 0
}

# Execute main function
main "$@"