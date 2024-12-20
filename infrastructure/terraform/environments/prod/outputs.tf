# Core Terraform functionality for output definitions
terraform {
  required_version = "~> 1.5"
}

# VPC Outputs
output "vpc_id" {
  description = "ID of the production VPC for resource association"
  value       = module.vpc.vpc_id
  sensitive   = false
}

output "vpc_private_subnets" {
  description = "List of private subnet IDs for application tier deployment"
  value       = module.vpc.private_subnet_ids
  sensitive   = false
}

output "vpc_database_subnets" {
  description = "List of database subnet IDs for RDS deployment"
  value       = module.vpc.database_subnet_ids
  sensitive   = false
}

output "vpc_availability_zones" {
  description = "List of availability zones used by the VPC for HA deployment"
  value       = module.vpc.availability_zones
  sensitive   = false
}

# Database Connection Details
output "database_connection" {
  description = "Database connection details for application configuration"
  value = {
    primary_endpoint = module.rds.primary_endpoint
    read_endpoints   = module.rds.replica_endpoints
    port            = module.rds.port
    engine_version  = module.rds.engine_version
  }
  sensitive = true # Marked sensitive to protect connection details
}

output "database_monitoring" {
  description = "Database monitoring configuration details"
  value = {
    instance_identifier = module.rds.instance_identifier
    security_group_id  = module.rds.security_group_id
    subnet_group_name  = module.rds.db_subnet_group_name
  }
  sensitive = false
}

# ECS Deployment Details
output "ecs_details" {
  description = "ECS cluster and service details for deployment and monitoring"
  value = {
    cluster_id   = module.ecs.cluster_id
    cluster_name = module.ecs.cluster_name
    service_id   = module.ecs.service_id
    service_name = module.ecs.service_name
  }
  sensitive = false
}

output "ecs_capacity" {
  description = "ECS cluster capacity configuration"
  value = {
    capacity_providers = module.ecs.cluster_capacity_providers
    desired_count     = module.ecs.service_desired_count
  }
  sensitive = false
}

# Service Discovery Endpoints
output "service_discovery" {
  description = "Service discovery endpoints for internal communication"
  value = {
    api_endpoint = "${module.ecs.service_name}.${var.environment}.local"
    db_endpoint  = module.rds.primary_endpoint
  }
  sensitive = false
}

# High Availability Configuration
output "ha_configuration" {
  description = "High availability deployment details"
  value = {
    multi_az_enabled     = true
    read_replica_count   = length(module.rds.replica_endpoints)
    availability_zones   = module.vpc.availability_zones
    deployment_strategy = {
      minimum_healthy_percent = 100
      maximum_percent        = 200
    }
  }
  sensitive = false
}

# Monitoring and Logging
output "monitoring_config" {
  description = "Monitoring and logging configuration details"
  value = {
    cloudwatch_log_group = "/ecs/${var.project_name}-${var.environment}"
    metrics_namespace    = "AWS/ECS"
    alarm_topics        = var.alarm_topics
  }
  sensitive = false
}

# Security Configuration
output "security_config" {
  description = "Security-related configuration details"
  value = {
    vpc_id            = module.vpc.vpc_id
    security_groups   = {
      ecs = module.ecs.service_security_group_id
      rds = module.rds.security_group_id
    }
    private_subnets   = module.vpc.private_subnet_ids
    database_subnets  = module.vpc.database_subnet_ids
  }
  sensitive = false
}

# Resource Tags
output "resource_tags" {
  description = "Common resource tags for the production environment"
  value = {
    Environment = var.environment
    Project     = var.project_name
    ManagedBy   = "terraform"
    DeployedAt  = timestamp()
  }
  sensitive = false
}