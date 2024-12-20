# Terraform variables definition file for AWS SES module
# Version: 1.5+
# Purpose: Defines configuration variables for AWS SES email service setup

# Required Variables

variable "environment" {
  description = "Deployment environment name (staging or production) for SES configuration"
  type        = string
  
  validation {
    condition     = contains(["staging", "production"], var.environment)
    error_message = "Environment must be either staging or production"
  }
}

variable "domain_name" {
  description = "Domain name for SES email configuration with DNS validation"
  type        = string
  
  validation {
    condition     = can(regex("^[a-z0-9][a-z0-9-]{1,61}[a-z0-9]\\.[a-z]{2,}$", var.domain_name))
    error_message = "Domain name must be a valid domain format"
  }
}

# Optional Variables with Defaults

variable "tags" {
  description = "Resource tags to apply to SES components for organization and tracking"
  type        = map(string)
  default = {
    Terraform   = "true"
    Module      = "ses"
    Service     = "email"
    Environment = "${var.environment}"
    ManagedBy   = "terraform"
  }
}

variable "enable_dkim" {
  description = "Enable DKIM signing for improved email deliverability and security"
  type        = bool
  default     = true
}

variable "enable_reputation_metrics" {
  description = "Enable SES reputation metrics tracking for monitoring email sending health"
  type        = bool
  default     = true
}

variable "configuration_set_name" {
  description = "Name of the SES configuration set for event tracking and reputation monitoring"
  type        = string
  default     = "transfer-system-${var.environment}"
  
  validation {
    condition     = can(regex("^[a-zA-Z0-9-_]+$", var.configuration_set_name))
    error_message = "Configuration set name must contain only alphanumeric characters, hyphens, and underscores"
  }
}