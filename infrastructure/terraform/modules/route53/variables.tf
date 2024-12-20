# Domain name variable for Route53 hosted zone configuration
variable "domain_name" {
  description = "The primary domain name for Route53 hosted zone (e.g., transfer-system.edu)"
  type        = string

  validation {
    condition     = can(regex("^[a-z0-9][a-z0-9-]{1,61}[a-z0-9]\\.[a-z]{2,}$", var.domain_name))
    error_message = "The domain_name value must be a valid domain name format."
  }
}

# Environment name variable for resource identification and tagging
variable "environment" {
  description = "Environment name for resource segregation (e.g., staging, production)"
  type        = string

  validation {
    condition     = contains(["development", "staging", "production", "dr"], var.environment)
    error_message = "Environment must be one of: development, staging, production, dr."
  }
}

# Health check enablement flag for Route53 endpoint monitoring
variable "health_check_enabled" {
  description = "Flag to enable or disable Route53 health checks for high availability monitoring"
  type        = bool
  default     = true
}

# Health check path for endpoint monitoring
variable "health_check_path" {
  description = "The endpoint path for Route53 health checks (e.g., /health)"
  type        = string
  default     = "/health"

  validation {
    condition     = can(regex("^/[a-zA-Z0-9-_/]*$", var.health_check_path))
    error_message = "The health_check_path must be a valid URL path starting with /."
  }
}

# Tags variable for consistent resource labeling
variable "tags" {
  description = "Map of tags to apply to all Route53 resources for better resource management"
  type        = map(string)
  default     = {}
}

# Failover configuration for high availability
variable "failover_enabled" {
  description = "Enable failover routing policy for high availability (99.9% uptime requirement)"
  type        = bool
  default     = true
}

# Health check interval for monitoring
variable "health_check_interval" {
  description = "The interval between health checks in seconds"
  type        = number
  default     = 30

  validation {
    condition     = var.health_check_interval >= 10 && var.health_check_interval <= 300
    error_message = "Health check interval must be between 10 and 300 seconds."
  }
}

# SSL/TLS certificate ARN for HTTPS validation
variable "certificate_arn" {
  description = "ARN of ACM certificate for HTTPS endpoints"
  type        = string
  default     = null

  validation {
    condition     = var.certificate_arn == null || can(regex("^arn:aws:acm:", var.certificate_arn))
    error_message = "Certificate ARN must be a valid ACM certificate ARN or null."
  }
}

# Latency-based routing configuration
variable "latency_routing_enabled" {
  description = "Enable latency-based routing for optimal request routing"
  type        = bool
  default     = true
}