#!/bin/bash

# collect-static.sh
# Version: 1.0.0
# Description: Production-grade script for collecting and deploying Django static files to AWS S3
# with CDN integration and monitoring capabilities.

set -euo pipefail

# Configuration
export DJANGO_SETTINGS_MODULE="config.settings.production"
LOG_DIR="/var/log/django"
LOG_FILE="${LOG_DIR}/static-collection.log"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
MAX_RETRIES=3
PARALLEL_JOBS=4

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Setup logging
setup_logging() {
    # Create log directory if it doesn't exist
    mkdir -p "${LOG_DIR}"
    
    # Ensure log file exists and is writable
    touch "${LOG_FILE}"
    chmod 644 "${LOG_FILE}"
    
    # Rotate logs if they exceed 100MB
    if [ -f "${LOG_FILE}" ] && [ $(stat -f%z "${LOG_FILE}") -gt 104857600 ]; then
        mv "${LOG_FILE}" "${LOG_FILE}.${TIMESTAMP}"
        gzip "${LOG_FILE}.${TIMESTAMP}"
    fi
    
    # Start new log section
    echo "=== Static Collection Started at $(date) ===" >> "${LOG_FILE}"
}

# Check prerequisites
check_prerequisites() {
    local status=0
    
    # Check AWS credentials
    if [ -z "${AWS_ACCESS_KEY_ID:-}" ] || [ -z "${AWS_SECRET_ACCESS_KEY:-}" ]; then
        echo -e "${RED}ERROR: AWS credentials not set${NC}"
        echo "ERROR: AWS credentials not set" >> "${LOG_FILE}"
        status=1
    fi
    
    # Check Django settings
    if ! python -c "from django.conf import settings; exit(0 if all([settings.STATIC_ROOT, settings.STATIC_URL, settings.AWS_STORAGE_BUCKET_NAME]) else 1)" 2>/dev/null; then
        echo -e "${RED}ERROR: Required Django settings are not properly configured${NC}"
        echo "ERROR: Required Django settings are not properly configured" >> "${LOG_FILE}"
        status=1
    fi
    
    # Check AWS S3 bucket accessibility
    if ! aws s3 ls "s3://${AWS_STORAGE_BUCKET_NAME}" >/dev/null 2>&1; then
        echo -e "${RED}ERROR: Cannot access S3 bucket${NC}"
        echo "ERROR: Cannot access S3 bucket" >> "${LOG_FILE}"
        status=1
    fi
    
    # Verify STATIC_ROOT directory
    if ! python -c "from django.conf import settings; exit(0 if os.path.exists(settings.STATIC_ROOT) or os.makedirs(settings.STATIC_ROOT, exist_ok=True) else 1)" 2>/dev/null; then
        echo -e "${RED}ERROR: Cannot create or access STATIC_ROOT directory${NC}"
        echo "ERROR: Cannot create or access STATIC_ROOT directory" >> "${LOG_FILE}"
        status=1
    fi
    
    return $status
}

# Clean up old files from S3
cleanup_old_files() {
    echo "Starting cleanup of old static files..."
    echo "Starting cleanup of old static files at $(date)" >> "${LOG_FILE}"
    
    # List current files in STATIC_ROOT
    local current_files=$(find "$(python -c 'from django.conf import settings; print(settings.STATIC_ROOT)')" -type f -printf '%P\n')
    
    # List files in S3
    local s3_files=$(aws s3 ls "s3://${AWS_STORAGE_BUCKET_NAME}/static/" --recursive | awk '{print $4}')
    
    # Compare and delete outdated files
    for s3_file in $s3_files; do
        if ! echo "$current_files" | grep -q "^${s3_file#static/}$"; then
            echo "Removing outdated file: $s3_file"
            aws s3 rm "s3://${AWS_STORAGE_BUCKET_NAME}/${s3_file}"
            echo "Removed outdated file: $s3_file" >> "${LOG_FILE}"
        fi
    done
}

# Invalidate CDN cache
invalidate_cdn_cache() {
    if [ -n "${AWS_S3_CUSTOM_DOMAIN:-}" ]; then
        echo "Invalidating CDN cache..."
        echo "Invalidating CDN cache at $(date)" >> "${LOG_FILE}"
        
        # Get CloudFront distribution ID
        local distribution_id=$(aws cloudfront list-distributions --query "DistributionList.Items[?DomainName=='${AWS_S3_CUSTOM_DOMAIN}'].Id" --output text)
        
        if [ -n "$distribution_id" ]; then
            aws cloudfront create-invalidation \
                --distribution-id "$distribution_id" \
                --paths "/static/*" \
                >> "${LOG_FILE}" 2>&1
            
            echo -e "${GREEN}CDN cache invalidation initiated${NC}"
        else
            echo -e "${YELLOW}WARNING: Could not find CloudFront distribution${NC}"
            echo "WARNING: Could not find CloudFront distribution" >> "${LOG_FILE}"
        fi
    fi
}

# Main collection function
collect_static() {
    local retry_count=0
    local exit_code=1
    
    echo "Starting static files collection..."
    echo "Starting static files collection at $(date)" >> "${LOG_FILE}"
    
    # Enable S3 transfer acceleration if configured
    if [ "$(python -c 'from django.conf import settings; print(getattr(settings, "AWS_S3_TRANSFER_ACCELERATION", False))')" = "True" ]; then
        export AWS_S3_ACCELERATE=true
    fi
    
    while [ $retry_count -lt $MAX_RETRIES ] && [ $exit_code -ne 0 ]; do
        if [ $retry_count -gt 0 ]; then
            echo -e "${YELLOW}Retrying collection (Attempt $((retry_count + 1))/${MAX_RETRIES})...${NC}"
            sleep 5
        fi
        
        # Run collectstatic with parallel processing
        python manage.py collectstatic --noinput \
            --parallel $PARALLEL_JOBS \
            --clear \
            --traceback \
            >> "${LOG_FILE}" 2>&1
        
        exit_code=$?
        retry_count=$((retry_count + 1))
    done
    
    if [ $exit_code -eq 0 ]; then
        echo -e "${GREEN}Static files collection completed successfully${NC}"
        echo "Static files collection completed successfully at $(date)" >> "${LOG_FILE}"
        
        # Cleanup and CDN invalidation
        cleanup_old_files
        invalidate_cdn_cache
        
        # Report collection statistics
        local total_files=$(find "$(python -c 'from django.conf import settings; print(settings.STATIC_ROOT)')" -type f | wc -l)
        local total_size=$(du -sh "$(python -c 'from django.conf import settings; print(settings.STATIC_ROOT)')" | cut -f1)
        
        echo -e "${GREEN}Collection Summary:${NC}"
        echo "Total files: $total_files"
        echo "Total size: $total_size"
        
        echo "Collection Summary:" >> "${LOG_FILE}"
        echo "Total files: $total_files" >> "${LOG_FILE}"
        echo "Total size: $total_size" >> "${LOG_FILE}"
    else
        echo -e "${RED}Static files collection failed after $MAX_RETRIES attempts${NC}"
        echo "Static files collection failed after $MAX_RETRIES attempts at $(date)" >> "${LOG_FILE}"
    fi
    
    return $exit_code
}

# Main execution
main() {
    # Setup logging first
    setup_logging
    
    # Check prerequisites
    if ! check_prerequisites; then
        echo -e "${RED}Prerequisite checks failed. Aborting.${NC}"
        echo "Prerequisite checks failed. Aborting at $(date)" >> "${LOG_FILE}"
        exit 1
    fi
    
    # Execute static collection
    if ! collect_static; then
        echo -e "${RED}Static collection failed. Check ${LOG_FILE} for details.${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}Static collection process completed successfully${NC}"
    echo "=== Static Collection Completed Successfully at $(date) ===" >> "${LOG_FILE}"
}

# Execute main function
main

```

This script provides a robust solution for collecting and deploying Django static files to AWS S3 with the following features:

1. Comprehensive error handling and logging
2. Prerequisite validation for AWS credentials and Django settings
3. Performance optimizations including parallel processing and S3 transfer acceleration
4. CDN cache invalidation
5. Cleanup of outdated files
6. Detailed logging with rotation
7. Multiple retry attempts for reliability
8. Collection statistics reporting
9. Color-coded console output
10. Production-grade safety checks

The script follows best practices for shell scripting including:
- Strict error handling with `set -euo pipefail`
- Comprehensive logging
- Clear output formatting
- Modular function design
- Proper exit code handling
- Environment variable validation
- Resource cleanup

Usage:
```bash
# Make script executable
chmod +x collect-static.sh

# Run script
./collect-static.sh