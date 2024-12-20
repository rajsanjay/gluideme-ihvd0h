# AWS Provider version ~> 5.0
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# Variables definition
variable "environment" {
  type        = string
  description = "Deployment environment identifier for resource naming and tagging"
}

variable "cluster_name" {
  type        = string
  description = "Identifier for the ElastiCache Redis cluster"
  default     = "redis-cache"
}

variable "vpc_id" {
  type        = string
  description = "VPC identifier for ElastiCache deployment"
}

variable "private_subnet_ids" {
  type        = list(string)
  description = "List of private subnet IDs for multi-AZ ElastiCache deployment"
}

variable "node_type" {
  type        = string
  description = "ElastiCache node instance type for performance scaling"
  default     = "cache.t3.medium"
}

variable "num_cache_clusters" {
  type        = number
  description = "Number of cache clusters for high availability"
  default     = 2
}

variable "engine_version" {
  type        = string
  description = "Redis engine version with feature compatibility"
  default     = "7.0"
}

variable "parameter_family" {
  type        = string
  description = "ElastiCache parameter group family for Redis configuration"
  default     = "redis7"
}

variable "maintenance_window" {
  type        = string
  description = "Weekly maintenance window for updates"
  default     = "sun:05:00-sun:06:00"
}

variable "snapshot_window" {
  type        = string
  description = "Daily backup window for snapshots"
  default     = "03:00-04:00"
}

variable "snapshot_retention_limit" {
  type        = number
  description = "Number of days to retain backup snapshots"
  default     = 7
}

variable "allowed_cidr_blocks" {
  type        = list(string)
  description = "CIDR blocks allowed to access Redis cluster"
}

variable "tags" {
  type        = map(string)
  description = "Resource tags for management and cost allocation"
  default     = {}
}

# Subnet group for multi-AZ deployment
resource "aws_elasticache_subnet_group" "main" {
  name       = "${var.environment}-${var.cluster_name}-subnet-group"
  subnet_ids = var.private_subnet_ids
  tags       = var.tags
}

# Parameter group for Redis optimization
resource "aws_elasticache_parameter_group" "main" {
  family = var.parameter_family
  name   = "${var.environment}-${var.cluster_name}-params"

  # Performance optimization parameters
  parameter {
    name  = "maxmemory-policy"
    value = "allkeys-lru"
  }

  parameter {
    name  = "notify-keyspace-events"
    value = "Ex"
  }

  tags = var.tags
}

# Security group for Redis access control
resource "aws_security_group" "redis" {
  name        = "${var.environment}-${var.cluster_name}-sg"
  description = "Security group for Redis cluster access"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 6379
    to_port     = 6379
    protocol    = "tcp"
    cidr_blocks = var.allowed_cidr_blocks
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(
    var.tags,
    {
      Name = "${var.environment}-${var.cluster_name}-sg"
    }
  )
}

# Redis replication group with multi-AZ support
resource "aws_elasticache_replication_group" "main" {
  replication_group_id          = "${var.environment}-${var.cluster_name}"
  description                   = "Redis cluster for Transfer Requirements System"
  node_type                     = var.node_type
  num_cache_clusters           = var.num_cache_clusters
  parameter_group_name         = aws_elasticache_parameter_group.main.name
  port                         = 6379
  subnet_group_name            = aws_elasticache_subnet_group.main.name
  security_group_ids           = [aws_security_group.redis.id]
  automatic_failover_enabled   = true
  multi_az_enabled            = true
  engine                       = "redis"
  engine_version              = var.engine_version
  maintenance_window          = var.maintenance_window
  snapshot_window             = var.snapshot_window
  snapshot_retention_limit    = var.snapshot_retention_limit
  at_rest_encryption_enabled  = true
  transit_encryption_enabled  = true
  auth_token_update_strategy = "ROTATE"
  auto_minor_version_upgrade = true

  tags = merge(
    var.tags,
    {
      Name = "${var.environment}-${var.cluster_name}"
    }
  )
}

# Output values for other modules
output "redis_primary_endpoint" {
  description = "Redis primary endpoint address"
  value       = aws_elasticache_replication_group.main.primary_endpoint_address
}

output "redis_reader_endpoint" {
  description = "Redis reader endpoint address"
  value       = aws_elasticache_replication_group.main.reader_endpoint_address
}

output "redis_port" {
  description = "Redis port number"
  value       = aws_elasticache_replication_group.main.port
}

output "redis_security_group_id" {
  description = "ID of the Redis security group"
  value       = aws_security_group.redis.id
}