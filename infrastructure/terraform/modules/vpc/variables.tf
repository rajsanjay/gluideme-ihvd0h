# Core Terraform functionality for variable definitions and validation
terraform {
  required_version = "~> 1.5"
}

# Environment variable with strict validation
variable "environment" {
  description = "Deployment environment (staging/production) with strict validation"
  type        = string
  
  validation {
    condition     = can(regex("^(staging|production)$", var.environment))
    error_message = "Environment must be either staging or production"
  }
}

# VPC CIDR block with strict IP range validation
variable "vpc_cidr" {
  description = "CIDR block for the VPC with strict IP range validation"
  type        = string
  
  validation {
    condition     = can(cidrhost(var.vpc_cidr, 0)) && can(regex("^10\\.\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}/16$", var.vpc_cidr))
    error_message = "VPC CIDR must be a valid IPv4 CIDR block in the 10.x.x.x/16 range"
  }
}

# Availability zones for high-availability deployment
variable "availability_zones" {
  description = "List of availability zones for high-availability deployment"
  type        = list(string)
  
  validation {
    condition     = length(var.availability_zones) >= 2 && length(var.availability_zones) <= 3
    error_message = "Between 2 and 3 availability zones must be specified for high availability"
  }
}

# Private subnet CIDRs with count validation
variable "private_subnet_cidrs" {
  description = "CIDR blocks for private subnets with count validation"
  type        = list(string)
  
  validation {
    condition     = length(var.private_subnet_cidrs) >= 2 && length(var.private_subnet_cidrs) == length(var.availability_zones)
    error_message = "Number of private subnet CIDRs must match the number of availability zones"
  }
}

# Database subnet CIDRs with strict validation
variable "database_subnet_cidrs" {
  description = "CIDR blocks for database subnets with strict validation"
  type        = list(string)
  
  validation {
    condition     = length(var.database_subnet_cidrs) >= 2 && length(var.database_subnet_cidrs) == length(var.availability_zones)
    error_message = "Number of database subnet CIDRs must match the number of availability zones"
  }
}

# NAT Gateway configuration for cost optimization
variable "single_nat_gateway" {
  description = "Whether to create a single NAT Gateway for all private subnets (cost optimization for non-production)"
  type        = bool
  default     = false
}

# VPC flow logs configuration for network monitoring
variable "enable_flow_logs" {
  description = "Enable VPC flow logs for network traffic monitoring"
  type        = bool
  default     = true
}

# Resource tagging configuration
variable "tags" {
  description = "Additional tags for VPC resources including environment and cost center"
  type        = map(string)
  default     = {}
}