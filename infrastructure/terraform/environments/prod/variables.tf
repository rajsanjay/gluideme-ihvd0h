# Core Terraform configuration
terraform {
  required_version = "~> 1.5"
}

# Project Information
variable "project_name" {
  type        = string
  description = "Name of the project used for resource naming"
  default     = "transfer-requirements"

  validation {
    condition     = can(regex("^[a-z0-9-]+$", var.project_name))
    error_message = "Project name must contain only lowercase letters, numbers, and hyphens"
  }
}

# Environment Configuration
variable "environment" {
  type        = string
  description = "Deployment environment identifier with strict production validation"
  default     = "production"

  validation {
    condition     = var.environment == "production"
    error_message = "Environment must be production for this configuration"
  }
}

# Region Configuration
variable "aws_region" {
  type        = string
  description = "AWS region for resource deployment with multi-AZ support"
  default     = "us-west-2"

  validation {
    condition     = contains(["us-west-2", "us-east-1"], var.aws_region)
    error_message = "Region must support all required services and multi-AZ deployment"
  }
}

# High Availability Configuration
variable "availability_zones" {
  type        = list(string)
  description = "List of availability zones for multi-AZ deployment with minimum requirement"
  default     = ["us-west-2a", "us-west-2b", "us-west-2c"]

  validation {
    condition     = length(var.availability_zones) >= 3
    error_message = "Production environment requires at least 3 availability zones"
  }
}

# VPC Configuration
variable "vpc_cidr" {
  type        = string
  description = "CIDR block for the VPC with strict IP range validation"
  default     = "10.0.0.0/16"

  validation {
    condition     = can(cidrhost(var.vpc_cidr, 0)) && can(regex("^10\\.\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}/16$", var.vpc_cidr))
    error_message = "VPC CIDR must be a valid IPv4 CIDR block in the 10.x.x.x/16 range"
  }
}

# RDS Configuration
variable "rds_instance_class" {
  type        = string
  description = "Production-grade RDS instance class"
  default     = "db.r6g.xlarge"

  validation {
    condition     = can(regex("^db\\.r6g\\.(xlarge|2xlarge|4xlarge)$", var.rds_instance_class))
    error_message = "Production RDS must use r6g.xlarge or larger"
  }
}

variable "rds_allocated_storage" {
  type        = number
  description = "Allocated storage in GB for RDS instances with minimum requirement"
  default     = 100

  validation {
    condition     = var.rds_allocated_storage >= 100
    error_message = "Production RDS requires minimum 100GB storage"
  }
}

variable "rds_multi_az" {
  type        = bool
  description = "Enable Multi-AZ deployment for RDS high availability"
  default     = true

  validation {
    condition     = var.rds_multi_az == true
    error_message = "Production RDS must have Multi-AZ enabled"
  }
}

# ECS Configuration
variable "ecs_task_cpu" {
  type        = number
  description = "CPU units for ECS tasks with production minimum"
  default     = 2048

  validation {
    condition     = var.ecs_task_cpu >= 2048
    error_message = "Production ECS tasks require minimum 2048 CPU units"
  }
}

variable "ecs_task_memory" {
  type        = number
  description = "Memory (MiB) for ECS tasks with production minimum"
  default     = 4096

  validation {
    condition     = var.ecs_task_memory >= 4096
    error_message = "Production ECS tasks require minimum 4096 MiB memory"
  }
}

variable "ecs_desired_count" {
  type        = number
  description = "Desired number of ECS tasks for high availability"
  default     = 4

  validation {
    condition     = var.ecs_desired_count >= 4
    error_message = "Production environment requires minimum 4 tasks for high availability"
  }
}

# Security Configuration
variable "backup_retention_days" {
  type        = number
  description = "Number of days to retain backups with compliance requirement"
  default     = 30

  validation {
    condition     = var.backup_retention_days >= 30
    error_message = "Production backup retention must be at least 30 days"
  }
}

variable "enable_encryption" {
  type        = bool
  description = "Enable encryption for all applicable resources"
  default     = true

  validation {
    condition     = var.enable_encryption == true
    error_message = "Production environment requires encryption enabled"
  }
}

# Monitoring Configuration
variable "enable_enhanced_monitoring" {
  type        = bool
  description = "Enable enhanced monitoring for production workloads"
  default     = true

  validation {
    condition     = var.enable_enhanced_monitoring == true
    error_message = "Production environment requires enhanced monitoring"
  }
}

# Auto Scaling Configuration
variable "auto_scaling_config" {
  type = object({
    min_capacity       = number
    max_capacity      = number
    cpu_threshold     = number
    memory_threshold  = number
  })
  description = "Auto scaling configuration for production workloads"
  default = {
    min_capacity      = 4
    max_capacity      = 12
    cpu_threshold     = 70
    memory_threshold  = 80
  }

  validation {
    condition     = var.auto_scaling_config.min_capacity >= 4
    error_message = "Production minimum capacity must be at least 4"
  }
}

# Resource Tags
variable "tags" {
  type        = map(string)
  description = "Resource tags for production environment"
  default = {
    Environment = "production"
    ManagedBy  = "terraform"
    Project    = "transfer-requirements"
  }
}