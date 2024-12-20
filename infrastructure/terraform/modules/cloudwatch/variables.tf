# Terraform variables configuration file for AWS CloudWatch module
# Defines monitoring, logging and alerting parameters for the Transfer Requirements Management System
# Version: ~> 1.5

# Environment name for deployment target
variable "environment" {
  description = "Deployment environment name (e.g. prod, staging, dev)"
  type        = string
  
  validation {
    condition     = can(regex("^(prod|staging|dev)$", var.environment))
    error_message = "Environment must be prod, staging, or dev"
  }
}

# Project name for resource naming
variable "project_name" {
  description = "Name of the project for resource naming and tagging"
  type        = string
  default     = "trms"
}

# Log retention configuration
variable "log_retention_days" {
  description = "Number of days to retain CloudWatch logs"
  type        = number
  default     = 90
  
  validation {
    condition     = var.log_retention_days >= 1 && var.log_retention_days <= 365
    error_message = "Log retention must be between 1 and 365 days"
  }
}

# Metric namespace
variable "metric_namespace" {
  description = "Namespace for CloudWatch metrics"
  type        = string
  default     = "TRMS"
}

# Alarm thresholds for different environments
variable "alarm_thresholds" {
  description = "Map of metric alarm thresholds"
  type = map(object({
    cpu_utilization    = number
    memory_utilization = number
    api_latency        = number
    error_rate         = number
  }))
  
  default = {
    prod = {
      cpu_utilization    = 70  # Warning threshold at 70% as per A.4.1
      memory_utilization = 80  # Warning threshold at 75% as per A.4.1
      api_latency        = 500 # Warning at 400ms as per A.4.1
      error_rate         = 1   # Warning at 1% as per A.4.1
    }
    staging = {
      cpu_utilization    = 80
      memory_utilization = 85
      api_latency        = 800
      error_rate         = 2
    }
  }
}

# Notification configuration
variable "notification_endpoints" {
  description = "List of SNS topic ARNs for alarm notifications"
  type        = list(string)
  default     = []
}

# Dashboard configuration
variable "dashboard_enabled" {
  description = "Whether to create CloudWatch dashboards"
  type        = bool
  default     = true
}

# Resource tagging
variable "tags" {
  description = "Additional tags for CloudWatch resources"
  type        = map(string)
  default     = {}
}