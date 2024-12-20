# Core project variables
variable "project" {
  type        = string
  description = "Project identifier for resource naming and tagging"
  default     = "trms"

  validation {
    condition     = can(regex("^[a-z0-9-]+$", var.project))
    error_message = "Project name must contain only lowercase letters, numbers, and hyphens"
  }
}

variable "environment" {
  type        = string
  description = "Deployment environment (prod, staging) with specific configurations"

  validation {
    condition     = can(regex("^(prod|staging)$", var.environment))
    error_message = "Environment must be either prod or staging"
  }
}

# Instance configuration variables
variable "instance_class" {
  type        = string
  description = "RDS instance type for performance optimization"
  default     = "db.r6g.xlarge"

  validation {
    condition     = can(regex("^db\\.(r6g|r6gd|r5)\\.", var.instance_class))
    error_message = "Must use r6g, r6gd, or r5 instance family for optimal performance"
  }
}

variable "engine_version" {
  type        = string
  description = "PostgreSQL engine version with minimum version requirement"
  default     = "14.7"

  validation {
    condition     = tonumber(split(".", var.engine_version)[0]) >= 14
    error_message = "PostgreSQL version must be 14.0 or higher"
  }
}

variable "allocated_storage" {
  type        = number
  description = "Allocated storage in GB with minimum size requirement"
  default     = 100

  validation {
    condition     = var.allocated_storage >= 100
    error_message = "Minimum storage size is 100 GB"
  }
}

# High availability configuration
variable "multi_az" {
  type        = bool
  description = "Enable Multi-AZ deployment for high availability"
  default     = true
}

variable "backup_retention_period" {
  type        = number
  description = "Backup retention period in days with minimum requirement"
  default     = 30

  validation {
    condition     = var.backup_retention_period >= 30
    error_message = "Minimum backup retention period is 30 days"
  }
}

variable "read_replica_count" {
  type        = number
  description = "Number of read replicas for performance optimization"
  default     = 2

  validation {
    condition     = var.read_replica_count >= 0 && var.read_replica_count <= 5
    error_message = "Read replica count must be between 0 and 5"
  }
}

# Network configuration
variable "vpc_id" {
  type        = string
  description = "VPC ID where RDS will be deployed"

  validation {
    condition     = can(regex("^vpc-", var.vpc_id))
    error_message = "VPC ID must be valid"
  }
}

variable "subnet_ids" {
  type        = list(string)
  description = "List of subnet IDs for RDS deployment across availability zones"

  validation {
    condition     = length(var.subnet_ids) >= 2
    error_message = "At least two subnets required for high availability"
  }
}

variable "vpc_cidr" {
  type        = string
  description = "VPC CIDR for security group rules"

  validation {
    condition     = can(cidrhost(var.vpc_cidr, 0))
    error_message = "Must be valid CIDR notation"
  }
}

# Security configuration
variable "kms_key_id" {
  type        = string
  description = "KMS key ID for RDS encryption at rest"

  validation {
    condition     = can(regex("^arn:aws:kms:", var.kms_key_id))
    error_message = "Must be valid KMS key ARN"
  }
}

# Database configuration
variable "parameter_group_family" {
  type        = string
  description = "DB parameter group family for PostgreSQL configuration"
  default     = "postgres14"

  validation {
    condition     = can(regex("^postgres[0-9]{2}$", var.parameter_group_family))
    error_message = "Must be valid PostgreSQL parameter group family"
  }
}