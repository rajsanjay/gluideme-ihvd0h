# Terraform variables configuration for staging environment
# Terraform version: ~> 1.5

# AWS Region Configuration
variable "aws_region" {
  type        = string
  description = "AWS region for staging environment deployment with single-AZ configuration"
  default     = "us-west-2"

  validation {
    condition     = can(regex("^[a-z]{2}-[a-z]+-\\d{1}$", var.aws_region))
    error_message = "AWS region must be a valid region identifier (e.g., us-west-2)"
  }
}

# Environment Identifier
variable "environment" {
  type        = string
  description = "Environment identifier - must be 'staging' for this configuration"
  default     = "staging"

  validation {
    condition     = var.environment == "staging"
    error_message = "Environment must be 'staging' for this configuration file"
  }
}

# Project Name
variable "project_name" {
  type        = string
  description = "Project name for resource naming and tagging - Transfer Requirements Management System"
  default     = "trms"
}

# VPC Configuration
variable "vpc_cidr" {
  type        = string
  description = "CIDR block for staging VPC network configuration"
  default     = "10.1.0.0/16"

  validation {
    condition     = can(cidrhost(var.vpc_cidr, 0))
    error_message = "VPC CIDR must be a valid IPv4 CIDR block"
  }
}

# RDS Configuration
variable "rds_instance_class" {
  type        = string
  description = "RDS instance class for staging environment - optimized for cost efficiency"
  default     = "db.r6g.large"
}

variable "rds_multi_az" {
  type        = bool
  description = "Multi-AZ deployment flag for RDS - disabled in staging for cost optimization"
  default     = false
}

variable "backup_retention_period" {
  type        = number
  description = "RDS backup retention period in days for staging environment"
  default     = 7
}

# ECS Configuration
variable "ecs_desired_count" {
  type        = number
  description = "Desired count of ECS tasks for staging environment"
  default     = 2
}

variable "ecs_container_cpu" {
  type        = number
  description = "CPU units for ECS containers (1024 = 1 vCPU)"
  default     = 1024
}

variable "ecs_container_memory" {
  type        = number
  description = "Memory (MiB) allocation for ECS containers"
  default     = 2048
}