# Terraform version constraint
terraform {
  required_version = "~> 1.5"
}

# Project name variable
variable "project_name" {
  type        = string
  description = "Name of the Transfer Requirements Management System project for resource naming and tagging"

  validation {
    condition     = length(var.project_name) > 0 && length(var.project_name) <= 64
    error_message = "Project name must be between 1 and 64 characters"
  }
}

# Environment variable
variable "environment" {
  type        = string
  description = "Deployment environment (staging/production) for resource tagging and configuration"

  validation {
    condition     = contains(["staging", "production"], var.environment)
    error_message = "Environment must be either staging or production"
  }
}

# Domain name variable
variable "domain_name" {
  type        = string
  description = "Primary domain name for the CloudFront distribution (e.g., transfer.university.edu)"

  validation {
    condition     = can(regex("^[a-z0-9][a-z0-9-]{1,61}[a-z0-9]\\.[a-z]{2,}$", var.domain_name))
    error_message = "Domain name must be a valid DNS name"
  }
}

# ACM certificate ARN variable
variable "certificate_arn" {
  type        = string
  description = "ARN of ACM certificate in us-east-1 for SSL/TLS termination at CloudFront edge locations"

  validation {
    condition     = can(regex("^arn:aws:acm:us-east-1:[0-9]{12}:certificate/[a-f0-9-]{36}$", var.certificate_arn))
    error_message = "Certificate ARN must be a valid ACM certificate ARN in us-east-1 region"
  }
}

# WAF Web ACL ID variable
variable "waf_web_acl_id" {
  type        = string
  description = "ID of WAF Web ACL for DDoS protection and request filtering"

  validation {
    condition     = can(regex("^[a-f0-9-]{36}$", var.waf_web_acl_id))
    error_message = "WAF Web ACL ID must be a valid UUID format"
  }
}

# Price class variable
variable "price_class" {
  type        = string
  description = "CloudFront distribution price class determining edge location coverage and cost"
  default     = "PriceClass_100"

  validation {
    condition     = contains(["PriceClass_100", "PriceClass_200", "PriceClass_All"], var.price_class)
    error_message = "Price class must be one of PriceClass_100, PriceClass_200, or PriceClass_All"
  }
}

# Default TTL variable
variable "default_ttl" {
  type        = number
  description = "Default Time To Live (TTL) in seconds for CloudFront cache to optimize origin load"
  default     = 3600

  validation {
    condition     = var.default_ttl >= 0 && var.default_ttl <= 31536000
    error_message = "Default TTL must be between 0 and 31536000 seconds (1 year)"
  }
}

# Minimum TTL variable
variable "min_ttl" {
  type        = number
  description = "Minimum Time To Live (TTL) in seconds for CloudFront cache"
  default     = 0

  validation {
    condition     = var.min_ttl >= 0 && var.min_ttl <= var.default_ttl
    error_message = "Minimum TTL must be between 0 and default TTL"
  }
}

# Maximum TTL variable
variable "max_ttl" {
  type        = number
  description = "Maximum Time To Live (TTL) in seconds for CloudFront cache"
  default     = 86400

  validation {
    condition     = var.max_ttl >= var.default_ttl && var.max_ttl <= 31536000
    error_message = "Maximum TTL must be between default TTL and 31536000 seconds (1 year)"
  }
}