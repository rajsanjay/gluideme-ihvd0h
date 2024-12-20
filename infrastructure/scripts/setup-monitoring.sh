#!/bin/bash

# Setup Monitoring Script for Transfer Requirements Management System
# Version: 1.0.0
# Dependencies:
# - docker-compose v2.20.0
# - prometheus v2.45.0
# - grafana v9.5.0
# - node-exporter v1.6.0
# - postgres-exporter v0.12.0

set -euo pipefail

# Global variables
readonly PROMETHEUS_VERSION="v2.45.0"
readonly GRAFANA_VERSION="9.5.0"
readonly MONITORING_DIR="/opt/monitoring"
readonly BACKUP_DIR="/opt/monitoring/backups"
readonly LOG_DIR="/opt/monitoring/logs"
readonly RETENTION_DAYS="90"
readonly ALERT_TIMEOUT="30"
readonly MAX_RETRIES="3"

# Logging setup
setup_logging() {
    local log_file="${LOG_DIR}/setup-$(date +%Y%m%d).log"
    mkdir -p "${LOG_DIR}"
    exec 1> >(tee -a "${log_file}")
    exec 2> >(tee -a "${log_file}" >&2)
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting monitoring setup..."
}

# Error handling
error_handler() {
    local line_no=$1
    local error_code=$2
    echo "[ERROR] Failed at line ${line_no} with error code ${error_code}"
    cleanup
    exit "${error_code}"
}

trap 'error_handler ${LINENO} $?' ERR

# Cleanup function
cleanup() {
    echo "Performing cleanup..."
    docker-compose down || true
    rm -f /tmp/monitoring_setup.* || true
}

# Check prerequisites
check_prerequisites() {
    echo "Checking prerequisites..."
    
    # Check if running as root
    if [[ $EUID -ne 0 ]]; then
        echo "This script must be run as root"
        exit 1
    }

    # Check required commands
    local required_commands=("docker" "docker-compose" "curl" "jq")
    for cmd in "${required_commands[@]}"; do
        if ! command -v "${cmd}" &> /dev/null; then
            echo "Required command not found: ${cmd}"
            exit 1
        fi
    done
}

# Create directory structure
create_directories() {
    echo "Creating directory structure..."
    local dirs=(
        "${MONITORING_DIR}"
        "${MONITORING_DIR}/prometheus"
        "${MONITORING_DIR}/prometheus/rules"
        "${MONITORING_DIR}/grafana"
        "${MONITORING_DIR}/grafana/dashboards"
        "${MONITORING_DIR}/grafana/provisioning"
        "${BACKUP_DIR}"
        "${LOG_DIR}"
    )

    for dir in "${dirs[@]}"; do
        mkdir -p "${dir}"
        chmod 750 "${dir}"
    done
}

# Setup Prometheus
setup_prometheus() {
    echo "Setting up Prometheus..."
    local config_path=$1
    local rules_path=$2
    local enable_ha=${3:-false}

    # Backup existing configuration
    if [[ -f "${MONITORING_DIR}/prometheus/prometheus.yml" ]]; then
        cp "${MONITORING_DIR}/prometheus/prometheus.yml" \
           "${BACKUP_DIR}/prometheus_$(date +%Y%m%d_%H%M%S).yml"
    fi

    # Copy and validate configuration
    cp "${config_path}" "${MONITORING_DIR}/prometheus/prometheus.yml"
    cp "${rules_path}" "${MONITORING_DIR}/prometheus/rules/alerts.yml"

    # Validate configuration
    docker run --rm \
        -v "${MONITORING_DIR}/prometheus:/etc/prometheus" \
        "prom/prometheus:${PROMETHEUS_VERSION}" \
        --config.file=/etc/prometheus/prometheus.yml \
        --check-config

    # Configure retention
    sed -i "s/retention.time: .*/retention.time: ${RETENTION_DAYS}d/" \
        "${MONITORING_DIR}/prometheus/prometheus.yml"

    # Setup HA if enabled
    if [[ "${enable_ha}" == "true" ]]; then
        setup_prometheus_ha
    fi
}

# Setup Grafana
setup_grafana() {
    echo "Setting up Grafana..."
    local admin_password=$1
    local datasource_config=$2
    local dashboard_paths=$3

    # Generate secure admin password if not provided
    if [[ -z "${admin_password}" ]]; then
        admin_password=$(openssl rand -base64 32)
        echo "Generated Grafana admin password: ${admin_password}"
    fi

    # Configure datasources
    mkdir -p "${MONITORING_DIR}/grafana/provisioning/datasources"
    cat > "${MONITORING_DIR}/grafana/provisioning/datasources/prometheus.yml" <<EOF
apiVersion: 1
datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: false
    version: 1
EOF

    # Configure dashboards
    mkdir -p "${MONITORING_DIR}/grafana/provisioning/dashboards"
    cp "${dashboard_paths}"/* "${MONITORING_DIR}/grafana/dashboards/"

    # Setup dashboard provisioning
    cat > "${MONITORING_DIR}/grafana/provisioning/dashboards/default.yml" <<EOF
apiVersion: 1
providers:
  - name: 'Default'
    orgId: 1
    folder: ''
    type: file
    disableDeletion: true
    editable: false
    options:
      path: /var/lib/grafana/dashboards
EOF

    # Configure Grafana security settings
    cat > "${MONITORING_DIR}/grafana/grafana.ini" <<EOF
[security]
admin_password = ${admin_password}
disable_gravatar = true
cookie_secure = true
cookie_samesite = strict
[auth]
disable_login_form = false
oauth_auto_login = false
[users]
allow_sign_up = false
[analytics]
reporting_enabled = false
check_for_updates = false
[snapshots]
external_enabled = false
EOF
}

# Setup exporters
setup_exporters() {
    echo "Setting up metric exporters..."
    
    # Node Exporter
    docker run -d \
        --name node-exporter \
        --restart unless-stopped \
        --net=host \
        --pid=host \
        -v "/:/host:ro,rslave" \
        quay.io/prometheus/node-exporter:v1.6.0 \
        --path.rootfs=/host

    # Postgres Exporter
    docker run -d \
        --name postgres-exporter \
        --restart unless-stopped \
        -p 9187:9187 \
        -e DATA_SOURCE_NAME="postgresql://postgres:password@postgres:5432/postgres?sslmode=disable" \
        quay.io/prometheus/postgres-exporter:v0.12.0
}

# Verify setup
verify_setup() {
    echo "Verifying monitoring setup..."
    local retry_count=0
    local max_retries=${MAX_RETRIES}

    # Check Prometheus
    while [[ ${retry_count} -lt ${max_retries} ]]; do
        if curl -s "http://localhost:9090/-/healthy" | grep -q "Prometheus is Healthy"; then
            echo "Prometheus is healthy"
            break
        fi
        ((retry_count++))
        sleep 5
    done

    # Check Grafana
    retry_count=0
    while [[ ${retry_count} -lt ${max_retries} ]]; do
        if curl -s "http://localhost:3000/api/health" | grep -q "ok"; then
            echo "Grafana is healthy"
            break
        fi
        ((retry_count++))
        sleep 5
    done

    # Verify exporters
    verify_exporter "node-exporter" 9100
    verify_exporter "postgres-exporter" 9187
}

# Helper function to verify exporter health
verify_exporter() {
    local exporter_name=$1
    local port=$2
    
    if curl -s "http://localhost:${port}/metrics" > /dev/null; then
        echo "${exporter_name} is healthy"
        return 0
    else
        echo "${exporter_name} health check failed"
        return 1
    fi
}

# Main execution
main() {
    setup_logging
    check_prerequisites
    create_directories

    # Setup components
    setup_prometheus \
        "../monitoring/prometheus/prometheus.yml" \
        "../monitoring/prometheus/rules/alerts.yml" \
        "false"

    setup_grafana \
        "${GRAFANA_ADMIN_PASSWORD:-}" \
        "../monitoring/grafana/provisioning/datasources" \
        "../monitoring/grafana/dashboards"

    setup_exporters

    # Start services
    docker-compose up -d

    # Verify setup
    verify_setup

    echo "Monitoring setup completed successfully"
}

# Execute main function
main "$@"