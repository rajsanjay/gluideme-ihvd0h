#!/bin/bash

# Database Backup Script for Transfer Requirements Management System
# Version: 1.0.0
# Performs encrypted PostgreSQL backups to AWS S3 with monitoring and retention management
# Requires: postgresql-client 14+, aws-cli 2.0+

set -euo pipefail

# Load environment variables and configuration
source /etc/environment

# Global configuration
BACKUP_BUCKET="${AWS_BACKUP_BUCKET}"
BACKUP_PREFIX="database/daily"
RETENTION_DAYS="90"
DB_HOST="${DB_HOST}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME}"
DB_USER="${DB_USER}"
DB_PASSWORD="${DB_PASSWORD}"
COMPRESSION_LEVEL="9"
KMS_KEY_ID="${KMS_KEY_ID}"
MULTIPART_THRESHOLD="100MB"
MAX_RETRIES="3"
CLOUDWATCH_NAMESPACE="DatabaseBackups"

# Configure logging
exec 1> >(logger -s -t $(basename $0)) 2>&1

# Utility functions
log() {
    echo "[$(date +'%Y-%m-%dT%H:%M:%S%z')]: $@"
}

error() {
    log "ERROR: $@" >&2
}

publish_metric() {
    local metric_name="$1"
    local value="$2"
    local unit="$3"
    
    aws cloudwatch put-metric-data \
        --namespace "${CLOUDWATCH_NAMESPACE}" \
        --metric-name "${metric_name}" \
        --value "${value}" \
        --unit "${unit}" \
        --dimensions "Environment=Production,Database=${DB_NAME}"
}

check_prerequisites() {
    local exit_code=0
    
    # Check required commands
    local required_commands=("pg_dump" "aws" "gzip" "md5sum")
    for cmd in "${required_commands[@]}"; do
        if ! command -v "${cmd}" >/dev/null 2>&1; then
            error "Required command not found: ${cmd}"
            exit_code=1
        fi
    done
    
    # Verify PostgreSQL version compatibility
    if ! pg_dump --version | grep -q "14\."; then
        error "PostgreSQL client version 14+ required"
        exit_code=1
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity >/dev/null 2>&1; then
        error "Invalid AWS credentials"
        exit_code=1
    fi
    
    # Verify KMS key access
    if ! aws kms describe-key --key-id "${KMS_KEY_ID}" >/dev/null 2>&1; then
        error "Cannot access KMS key: ${KMS_KEY_ID}"
        exit_code=1
    }
    
    # Check S3 bucket access
    if ! aws s3api head-bucket --bucket "${BACKUP_BUCKET}" 2>/dev/null; then
        error "Cannot access S3 bucket: ${BACKUP_BUCKET}"
        exit_code=1
    fi
    
    # Verify database connectivity
    if ! PGPASSWORD="${DB_PASSWORD}" pg_dump -h "${DB_HOST}" -p "${DB_PORT}" \
        -U "${DB_USER}" -d "${DB_NAME}" -v -F c -f /dev/null >/dev/null 2>&1; then
        error "Cannot connect to database"
        exit_code=1
    fi
    
    # Check available disk space (need at least 20GB free)
    local free_space=$(df -BG /tmp | awk 'NR==2 {print $4}' | sed 's/G//')
    if [ "${free_space}" -lt 20 ]; then
        error "Insufficient disk space. Required: 20GB, Available: ${free_space}GB"
        exit_code=1
    fi
    
    return ${exit_code}
}

create_backup() {
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="/tmp/backup_${DB_NAME}_${timestamp}.pgdump"
    local start_time=$(date +%s)
    
    log "Starting database backup to ${backup_file}"
    
    # Create backup with progress monitoring
    PGPASSWORD="${DB_PASSWORD}" pg_dump \
        -h "${DB_HOST}" \
        -p "${DB_PORT}" \
        -U "${DB_USER}" \
        -d "${DB_NAME}" \
        -v \
        -F c \
        -Z "${COMPRESSION_LEVEL}" \
        -f "${backup_file}" 2>&1 | \
    while IFS= read -r line; do
        log "${line}"
    done
    
    if [ ! -f "${backup_file}" ]; then
        error "Backup file was not created"
        return 1
    }
    
    # Calculate backup size and duration
    local backup_size=$(stat -f %z "${backup_file}")
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    # Generate backup checksum
    local backup_md5=$(md5sum "${backup_file}" | cut -d' ' -f1)
    
    # Publish metrics
    publish_metric "BackupSize" "${backup_size}" "Bytes"
    publish_metric "BackupDuration" "${duration}" "Seconds"
    
    echo "${backup_file}:${backup_md5}"
}

upload_backup() {
    local backup_info="$1"
    local backup_file=$(echo "${backup_info}" | cut -d: -f1)
    local backup_md5=$(echo "${backup_info}" | cut -d: -f2)
    local backup_key="${BACKUP_PREFIX}/$(basename ${backup_file})"
    local start_time=$(date +%s)
    
    log "Uploading backup to s3://${BACKUP_BUCKET}/${backup_key}"
    
    # Upload with server-side encryption and metadata
    aws s3 cp "${backup_file}" "s3://${BACKUP_BUCKET}/${backup_key}" \
        --sse aws:kms \
        --sse-kms-key-id "${KMS_KEY_ID}" \
        --metadata "md5checksum=${backup_md5}" \
        --expected-size $(stat -f %z "${backup_file}") \
        --storage-class STANDARD_IA \
        --metadata-directive REPLACE
    
    # Verify upload
    local uploaded_md5=$(aws s3api head-object \
        --bucket "${BACKUP_BUCKET}" \
        --key "${backup_key}" \
        --query 'Metadata.md5checksum' \
        --output text)
    
    if [ "${uploaded_md5}" != "${backup_md5}" ]; then
        error "Upload verification failed: MD5 mismatch"
        return 1
    }
    
    local end_time=$(date +%s)
    publish_metric "UploadDuration" "$((end_time - start_time))" "Seconds"
    
    log "Backup uploaded successfully"
    return 0
}

cleanup_old_backups() {
    local retention_date=$(date -v-${RETENTION_DAYS}d +%Y-%m-%d)
    
    log "Cleaning up backups older than ${retention_date}"
    
    # List and delete old backups
    aws s3api list-objects-v2 \
        --bucket "${BACKUP_BUCKET}" \
        --prefix "${BACKUP_PREFIX}/" \
        --query "Contents[?LastModified<='${retention_date}'].Key" \
        --output text | \
    while read -r key; do
        if [ ! -z "${key}" ]; then
            log "Deleting old backup: ${key}"
            aws s3 rm "s3://${BACKUP_BUCKET}/${key}"
        fi
    done
    
    # Update retention metrics
    local remaining_backups=$(aws s3api list-objects-v2 \
        --bucket "${BACKUP_BUCKET}" \
        --prefix "${BACKUP_PREFIX}/" \
        --query 'length(Contents)' \
        --output text)
    
    publish_metric "RetainedBackups" "${remaining_backups}" "Count"
}

main() {
    local exit_code=0
    local backup_file=""
    
    log "Starting backup process"
    
    # Check prerequisites
    if ! check_prerequisites; then
        error "Prerequisite check failed"
        return 1
    fi
    
    # Create backup
    local backup_info=$(create_backup)
    if [ $? -ne 0 ]; then
        error "Backup creation failed"
        return 1
    fi
    
    # Upload backup
    if ! upload_backup "${backup_info}"; then
        error "Backup upload failed"
        exit_code=1
    fi
    
    # Cleanup old backups
    if ! cleanup_old_backups; then
        error "Backup cleanup failed"
        exit_code=1
    fi
    
    # Cleanup temporary files
    backup_file=$(echo "${backup_info}" | cut -d: -f1)
    if [ -f "${backup_file}" ]; then
        rm -f "${backup_file}"
    fi
    
    log "Backup process completed with exit code ${exit_code}"
    return ${exit_code}
}

# Execute main function
main