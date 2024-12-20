# Environment configuration
variable "environment" {
  type        = string
  description = "Deployment environment name (e.g., prod, staging, dev)"
  
  validation {
    condition     = contains(["prod", "staging", "dev"], var.environment)
    error_message = "Environment must be one of: prod, staging, dev."
  }
}

# Cluster naming
variable "cluster_name" {
  type        = string
  description = "Name prefix for the ElastiCache Redis cluster resources"
  default     = "trms-redis-cache"
  
  validation {
    condition     = can(regex("^trms-[a-zA-Z0-9-]{3,40}$", var.cluster_name))
    error_message = "Cluster name must start with 'trms-' and be between 3-40 characters."
  }
}

# Network configuration
variable "vpc_id" {
  type        = string
  description = "ID of the VPC where ElastiCache cluster will be deployed"
  
  validation {
    condition     = can(regex("^vpc-[a-z0-9]+$", var.vpc_id))
    error_message = "VPC ID must be a valid AWS VPC ID starting with 'vpc-'."
  }
}

variable "private_subnet_ids" {
  type        = list(string)
  description = "List of private subnet IDs for multi-AZ ElastiCache deployment"
  
  validation {
    condition     = length(var.private_subnet_ids) >= 2
    error_message = "At least 2 private subnet IDs are required for high availability deployment."
  }
}

# Instance configuration
variable "node_type" {
  type        = string
  description = "ElastiCache node instance type for optimal performance/cost balance"
  default     = "cache.r6g.xlarge"
  
  validation {
    condition     = can(regex("^cache\\.r6g\\.[a-z0-9]+$", var.node_type))
    error_message = "Node type must be a valid ElastiCache r6g instance type."
  }
}

variable "num_cache_clusters" {
  type        = number
  description = "Number of cache clusters for high availability (minimum 2 for multi-AZ)"
  default     = 2
  
  validation {
    condition     = var.num_cache_clusters >= 2
    error_message = "Number of cache clusters must be >= 2 for production environments."
  }
}

# Redis configuration
variable "engine_version" {
  type        = string
  description = "Redis engine version (must be 7.0 or higher for required features)"
  default     = "7.0"
  
  validation {
    condition     = tonumber(var.engine_version) >= 7.0
    error_message = "Redis engine version must be >= 7.0 for required functionality."
  }
}

variable "parameter_group_family" {
  type        = string
  description = "ElastiCache parameter group family matching Redis version"
  default     = "redis7"
  
  validation {
    condition     = can(regex("^redis[0-9]+$", var.parameter_group_family))
    error_message = "Parameter group family must match the Redis engine version."
  }
}

# Maintenance configuration
variable "maintenance_window" {
  type        = string
  description = "Weekly maintenance window in UTC (recommended during low-traffic periods)"
  default     = "sun:05:00-sun:06:00"
  
  validation {
    condition     = can(regex("^[a-z]{3}:[0-9]{2}:[0-9]{2}-[a-z]{3}:[0-9]{2}:[0-9]{2}$", var.maintenance_window))
    error_message = "Maintenance window must be in format day:HH:mm-day:HH:mm."
  }
}

variable "snapshot_window" {
  type        = string
  description = "Daily snapshot window in UTC (should not overlap with maintenance window)"
  default     = "03:00-04:00"
  
  validation {
    condition     = can(regex("^[0-9]{2}:[0-9]{2}-[0-9]{2}:[0-9]{2}$", var.snapshot_window))
    error_message = "Snapshot window must be in format HH:mm-HH:mm."
  }
}

variable "snapshot_retention_limit" {
  type        = number
  description = "Number of days to retain automatic snapshots (0 to disable)"
  default     = 7
  
  validation {
    condition     = var.snapshot_retention_limit >= 0 && var.snapshot_retention_limit <= 35
    error_message = "Snapshot retention limit must be between 0 and 35 days."
  }
}

# Network and security configuration
variable "port" {
  type        = number
  description = "Port number for Redis connections"
  default     = 6379
  
  validation {
    condition     = var.port >= 1024 && var.port <= 65535
    error_message = "Port must be between 1024 and 65535."
  }
}

variable "allowed_cidr_blocks" {
  type        = list(string)
  description = "List of CIDR blocks allowed to access the Redis cluster"
  default     = []
  
  validation {
    condition     = alltrue([for cidr in var.allowed_cidr_blocks : can(cidrhost(cidr, 0))])
    error_message = "All entries must be valid CIDR blocks."
  }
}

# Security features
variable "automatic_failover_enabled" {
  type        = bool
  description = "Enable automatic failover for multi-AZ deployments"
  default     = true
  
  validation {
    condition     = var.automatic_failover_enabled
    error_message = "Automatic failover must be enabled for production environments."
  }
}

variable "at_rest_encryption_enabled" {
  type        = bool
  description = "Enable encryption at rest for Redis cluster"
  default     = true
  
  validation {
    condition     = var.at_rest_encryption_enabled
    error_message = "Encryption at rest must be enabled for production environments."
  }
}

variable "transit_encryption_enabled" {
  type        = bool
  description = "Enable TLS for Redis connections"
  default     = true
  
  validation {
    condition     = var.transit_encryption_enabled
    error_message = "Transit encryption must be enabled for production environments."
  }
}

# Resource tagging
variable "tags" {
  type        = map(string)
  description = "Resource tags for cost allocation and resource management"
  default     = {}
  
  validation {
    condition     = alltrue([for k, v in var.tags : can(tostring(v))])
    error_message = "All tag values must be strings."
  }
}