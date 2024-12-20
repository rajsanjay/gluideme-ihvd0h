#!/bin/bash

# Transfer Requirements Management System - Secret Rotation Script
# Version: 1.0.0
# Handles automated rotation of sensitive credentials with enhanced security,
# backup, validation, and monitoring capabilities.

set -euo pipefail

# Import AWS utility functions
source "$(dirname "$0")/../../src/backend/utils/aws.py"

# Global Configuration
AWS_REGION=${AWS_REGION:-"us-west-2"}
ENVIRONMENT=${ENVIRONMENT:-"production"}
LOG_FILE=${LOG_FILE:-"/var/log/secret-rotation.log"}
BACKUP_RETENTION_DAYS=${BACKUP_RETENTION_DAYS:-90}
MAX_RETRY_ATTEMPTS=${MAX_RETRY_ATTEMPTS:-3}
ALERT_WEBHOOK_URL=${ALERT_WEBHOOK_URL:-""}

# S3 backup configuration
BACKUP_BUCKET="trms-secret-backups-${ENVIRONMENT}"
BACKUP_PREFIX="rotations/$(date +%Y/%m/%d)"
KMS_KEY_ALIAS="alias/trms-secret-rotation-${ENVIRONMENT}"

# Logging configuration
setup_logging() {
    local timestamp=$(date +"%Y-%m-%d %H:%M:%S")
    local log_dir=$(dirname "$LOG_FILE")
    
    # Ensure log directory exists with proper permissions
    mkdir -p "$log_dir"
    chmod 750 "$log_dir"
    
    # Initialize log file with rotation
    if [ ! -f "$LOG_FILE" ]; then
        touch "$LOG_FILE"
        chmod 640 "$LOG_FILE"
    fi
    
    # Rotate logs if they exceed 100MB
    if [ -f "$LOG_FILE" ] && [ $(stat -f%z "$LOG_FILE") -gt 104857600 ]; then
        mv "$LOG_FILE" "${LOG_FILE}.$(date +%s)"
        gzip "${LOG_FILE}.$(date +%s)"
    fi
    
    exec 1> >(tee -a "$LOG_FILE")
    exec 2> >(tee -a "$LOG_FILE" >&2)
    
    echo "[$timestamp] Starting secret rotation process for environment: $ENVIRONMENT"
}

# Validate prerequisites before rotation
validate_prerequisites() {
    local validation_errors=()
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &>/dev/null; then
        validation_errors+=("Invalid AWS credentials")
    fi
    
    # Verify KMS key access
    if ! aws kms describe-key --key-id "$KMS_KEY_ALIAS" &>/dev/null; then
        validation_errors+=("Cannot access KMS key: $KMS_KEY_ALIAS")
    fi
    
    # Check S3 backup bucket
    if ! aws s3api head-bucket --bucket "$BACKUP_BUCKET" &>/dev/null; then
        validation_errors+=("Cannot access backup bucket: $BACKUP_BUCKET")
    fi
    
    # Verify monitoring connectivity
    if [ -n "$ALERT_WEBHOOK_URL" ] && ! curl -s -o /dev/null "$ALERT_WEBHOOK_URL"; then
        validation_errors+=("Cannot connect to monitoring webhook")
    fi
    
    if [ ${#validation_errors[@]} -gt 0 ]; then
        echo "Prerequisite validation failed:"
        printf '%s\n' "${validation_errors[@]}"
        return 1
    fi
    
    return 0
}

# Create encrypted backup of current secrets
backup_secrets() {
    local backup_id="rotation-$(date +%Y%m%d-%H%M%S)-$(openssl rand -hex 4)"
    local backup_file="/tmp/$backup_id.json"
    local encrypted_backup="/tmp/$backup_id.enc"
    
    echo "Creating encrypted backup of current secrets..."
    
    # Collect current secrets
    aws secretsmanager list-secrets \
        --filters Key=tag-key,Values="Environment",Key=tag-value,Values="$ENVIRONMENT" \
        | jq -r '.SecretList[] | {id: .ARN, name: .Name}' > "$backup_file"
        
    # Fetch and store secret values
    while read -r secret; do
        local secret_id=$(echo "$secret" | jq -r '.id')
        local secret_name=$(echo "$secret" | jq -r '.name')
        
        aws secretsmanager get-secret-value --secret-id "$secret_id" \
            | jq --arg name "$secret_name" '{name: $name, value: .SecretString}' \
            >> "$backup_file"
    done < <(jq -c '.' "$backup_file")
    
    # Encrypt backup using KMS
    aws kms encrypt \
        --key-id "$KMS_KEY_ALIAS" \
        --plaintext "fileb://$backup_file" \
        --output text --query CiphertextBlob > "$encrypted_backup"
        
    # Upload to S3 with metadata
    aws s3 cp "$encrypted_backup" \
        "s3://$BACKUP_BUCKET/$BACKUP_PREFIX/$backup_id.enc" \
        --metadata "rotation-id=$backup_id,environment=$ENVIRONMENT" \
        --sse aws:kms \
        --sse-kms-key-id "$KMS_KEY_ALIAS"
        
    # Cleanup temporary files
    shred -u "$backup_file" "$encrypted_backup"
    
    echo "Backup created successfully: $backup_id"
    return 0
}

# Rotate database credentials
rotate_database_credentials() {
    local db_identifier=$1
    local retry_count=0
    local rotation_successful=false
    
    echo "Rotating credentials for database: $db_identifier"
    
    while [ $retry_count -lt $MAX_RETRY_ATTEMPTS ] && [ "$rotation_successful" = false ]; do
        # Generate secure password
        local new_password=$(openssl rand -base64 32 | tr -dc 'a-zA-Z0-9!@#$%^&*()_+=' | head -c 32)
        
        # Create temporary credentials for validation
        if aws rds modify-db-instance \
            --db-instance-identifier "$db_identifier" \
            --master-user-password "$new_password" \
            --apply-immediately; then
            
            # Wait for DB modification to complete
            aws rds wait db-instance-available \
                --db-instance-identifier "$db_identifier"
            
            # Validate new credentials
            if PGPASSWORD="$new_password" psql -h "$db_identifier" -U master -c "\l" &>/dev/null; then
                rotation_successful=true
                
                # Update secret in AWS Secrets Manager
                aws secretsmanager update-secret \
                    --secret-id "trms/database/$ENVIRONMENT/$db_identifier" \
                    --secret-string "{\"username\":\"master\",\"password\":\"$new_password\"}"
                
                echo "Successfully rotated credentials for $db_identifier"
            fi
        fi
        
        if [ "$rotation_successful" = false ]; then
            retry_count=$((retry_count + 1))
            echo "Rotation attempt $retry_count failed, retrying..."
            sleep 5
        fi
    done
    
    if [ "$rotation_successful" = false ]; then
        handle_rotation_failure "Database credential rotation failed" \
            "{\"database\":\"$db_identifier\",\"attempts\":$retry_count}"
        return 1
    fi
    
    return 0
}

# Handle rotation failures
handle_rotation_failure() {
    local failure_message=$1
    local error_details=$2
    local timestamp=$(date +"%Y-%m-%d %H:%M:%S")
    
    echo "[$timestamp] ERROR: $failure_message"
    
    # Log error details
    logger -p user.err "Secret rotation failure: $failure_message - $error_details"
    
    # Send alert if webhook configured
    if [ -n "$ALERT_WEBHOOK_URL" ]; then
        curl -X POST "$ALERT_WEBHOOK_URL" \
            -H "Content-Type: application/json" \
            -d "{
                \"severity\": \"high\",
                \"environment\": \"$ENVIRONMENT\",
                \"message\": \"$failure_message\",
                \"details\": $error_details,
                \"timestamp\": \"$timestamp\"
            }"
    fi
    
    # Create incident ticket
    aws sns publish \
        --topic-arn "arn:aws:sns:$AWS_REGION:$(aws sts get-caller-identity --query Account --output text):trms-incidents-$ENVIRONMENT" \
        --message "Secret rotation failure: $failure_message - $error_details" \
        --subject "Secret Rotation Failure - $ENVIRONMENT"
        
    return 1
}

# Cleanup old backups
cleanup_old_backups() {
    echo "Cleaning up old secret backups..."
    
    aws s3 ls "s3://$BACKUP_BUCKET/rotations/" \
        | while read -r line; do
            backup_date=$(echo "$line" | awk '{print $1}')
            days_old=$(( ( $(date +%s) - $(date -d "$backup_date" +%s) ) / 86400 ))
            
            if [ $days_old -gt $BACKUP_RETENTION_DAYS ]; then
                aws s3 rm "s3://$BACKUP_BUCKET/rotations/$backup_date" --recursive
            fi
        done
}

# Main rotation process
main() {
    setup_logging
    
    if ! validate_prerequisites; then
        handle_rotation_failure "Failed prerequisite validation" "{}"
        exit 1
    fi
    
    # Create backup before rotation
    if ! backup_secrets; then
        handle_rotation_failure "Failed to create backup" "{}"
        exit 1
    fi
    
    # Rotate database credentials
    if ! rotate_database_credentials "trms-primary-$ENVIRONMENT"; then
        exit 1
    fi
    
    # Cleanup old backups
    cleanup_old_backups
    
    echo "Secret rotation completed successfully"
    exit 0
}

# Execute main function
main "$@"