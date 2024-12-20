# Core Terraform functionality for variable definitions
terraform {
  required_version = "~> 1.5"
}

# Environment variable with validation for allowed values
variable "environment" {
  type        = string
  description = "Deployment environment (e.g., prod, staging, dev)"

  validation {
    condition     = can(regex("^(prod|staging|dev)$", var.environment))
    error_message = "Environment must be prod, staging, or dev"
  }
}

# Rate limiting configuration with reasonable defaults and validation
variable "rate_limit_threshold" {
  type        = number
  description = "Maximum number of requests allowed per 5-minute period per IP"
  default     = 2000

  validation {
    condition     = var.rate_limit_threshold >= 100 && var.rate_limit_threshold <= 10000
    error_message = "Rate limit threshold must be between 100 and 10000"
  }
}

# WAF logging configuration
variable "enable_logging" {
  type        = bool
  description = "Enable WAF logging to CloudWatch"
  default     = true
}

# Log retention configuration with validation for allowed CloudWatch values
variable "log_retention_days" {
  type        = number
  description = "Number of days to retain WAF logs in CloudWatch"
  default     = 30

  validation {
    condition = contains([
      0, 1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1827, 3653
    ], var.log_retention_days)
    error_message = "Log retention days must be a valid CloudWatch Logs retention period"
  }
}

# Geo-blocking configuration
variable "block_high_risk_countries" {
  type        = bool
  description = "Enable blocking of high-risk countries"
  default     = true
}

variable "high_risk_countries" {
  type        = list(string)
  description = "List of country codes to block when block_high_risk_countries is true"
  default     = []

  validation {
    condition     = alltrue([for country in var.high_risk_countries : can(regex("^[A-Z]{2}$", country))])
    error_message = "Country codes must be valid 2-letter ISO country codes in uppercase"
  }
}

# Resource tagging
variable "tags" {
  type        = map(string)
  description = "Resource tags for WAF resources"
  default     = {}

  validation {
    condition     = length(var.tags) <= 50
    error_message = "Maximum of 50 tags are allowed for AWS resources"
  }
}