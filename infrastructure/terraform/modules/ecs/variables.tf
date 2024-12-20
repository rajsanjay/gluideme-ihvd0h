# terraform ~> 1.5

# Project Information
variable "project_name" {
  description = "Name of the project used for resource naming"
  type        = string

  validation {
    condition     = length(var.project_name) > 0
    error_message = "Project name cannot be empty"
  }
}

variable "environment" {
  description = "Deployment environment (prod, staging)"
  type        = string

  validation {
    condition     = contains(["prod", "staging"], var.environment)
    error_message = "Environment must be either prod or staging"
  }
}

# Network Configuration
variable "vpc_id" {
  description = "ID of the VPC where ECS resources will be deployed"
  type        = string

  validation {
    condition     = can(regex("^vpc-", var.vpc_id))
    error_message = "VPC ID must be valid"
  }
}

variable "private_subnets" {
  description = "List of private subnet IDs for ECS task deployment"
  type        = list(string)

  validation {
    condition     = length(var.private_subnets) >= 2
    error_message = "At least 2 private subnets required for HA"
  }
}

# Task Configuration
variable "task_cpu" {
  description = "CPU units for ECS task (1024 = 1 vCPU)"
  type        = number
  default     = 1024

  validation {
    condition     = contains([256, 512, 1024, 2048, 4096], var.task_cpu)
    error_message = "CPU units must be valid Fargate values"
  }
}

variable "task_memory" {
  description = "Memory (MB) for ECS task"
  type        = number
  default     = 2048

  validation {
    condition     = var.task_memory >= 512 && var.task_memory <= 30720
    error_message = "Memory must be between 512MB and 30GB"
  }
}

variable "desired_count" {
  description = "Desired number of ECS tasks to run"
  type        = number
  default     = 2

  validation {
    condition     = var.desired_count > 0
    error_message = "Desired count must be greater than 0"
  }
}

# Auto-scaling Configuration
variable "cpu_threshold" {
  description = "CPU utilization threshold for auto-scaling"
  type        = number
  default     = 70

  validation {
    condition     = var.cpu_threshold > 0 && var.cpu_threshold <= 100
    error_message = "CPU threshold must be between 1 and 100"
  }
}

variable "memory_threshold" {
  description = "Memory utilization threshold for auto-scaling"
  type        = number
  default     = 80

  validation {
    condition     = var.memory_threshold > 0 && var.memory_threshold <= 100
    error_message = "Memory threshold must be between 1 and 100"
  }
}

# Container Configuration
variable "container_image" {
  description = "Docker image for ECS task"
  type        = string

  validation {
    condition     = length(var.container_image) > 0
    error_message = "Container image must be specified"
  }
}

variable "container_port" {
  description = "Port exposed by the container"
  type        = number
  default     = 8000

  validation {
    condition     = var.container_port > 0 && var.container_port <= 65535
    error_message = "Container port must be between 1 and 65535"
  }
}

variable "health_check_path" {
  description = "Path for container health checks"
  type        = string
  default     = "/health"

  validation {
    condition     = startswith(var.health_check_path, "/")
    error_message = "Health check path must start with /"
  }
}

# Resource Tagging
variable "tags" {
  description = "Resource tags"
  type        = map(string)
  default     = {}

  validation {
    condition     = can(var.tags)
    error_message = "Tags must be a valid map of strings"
  }
}