# Terraform outputs for staging environment infrastructure
# Exposes essential infrastructure details for external consumption
# while maintaining security and supporting single-AZ configurations

terraform {
  # Enforce minimum Terraform version for consistent deployments
  required_version = "~> 1.5"
}

# VPC Outputs
output "vpc_id" {
  description = "ID of the VPC hosting the staging environment infrastructure"
  value       = module.vpc.vpc_id
  sensitive   = false
}

output "private_subnet_ids" {
  description = "List of private subnet IDs where ECS services are deployed in single-AZ configuration"
  value       = module.vpc.private_subnet_ids
  sensitive   = false
}

output "database_subnet_ids" {
  description = "List of database subnet IDs where single-AZ RDS instance is deployed"
  value       = module.vpc.database_subnet_ids
  sensitive   = false
}

# ECS Cluster Outputs
output "ecs_cluster_id" {
  description = "ID of the ECS cluster running staging workloads"
  value       = module.ecs.cluster_id
  sensitive   = false
}

output "ecs_cluster_name" {
  description = "Name of the ECS cluster for staging environment service discovery"
  value       = module.ecs.cluster_name
  sensitive   = false
}

output "ecs_service_name" {
  description = "Name of the ECS service running the staging application workload"
  value       = module.ecs.service_name
  sensitive   = false
}

output "service_discovery_endpoint" {
  description = "Service discovery endpoint for container-to-container communication in staging"
  value       = module.ecs.service_discovery_endpoint
  sensitive   = false
}

output "task_execution_role_arn" {
  description = "ARN of the IAM role used for ECS task execution in staging"
  value       = module.ecs.task_execution_role_arn
  sensitive   = false
}

# Database Outputs
output "database_endpoint" {
  description = "Connection endpoint for the single-AZ RDS instance in staging"
  value       = module.rds.db_endpoint
  sensitive   = true # Marked sensitive to protect database connection details
}

output "database_instance_id" {
  description = "Instance identifier for the RDS database in staging"
  value       = module.rds.db_instance_id
  sensitive   = false
}

output "database_port" {
  description = "Port number for RDS instance connections in staging"
  value       = module.rds.db_port
  sensitive   = true # Marked sensitive to protect database connection details
}

# Composite Output for External Service Integration
output "staging_infrastructure" {
  description = "Combined infrastructure details for staging environment service integration"
  value = {
    vpc_id                     = module.vpc.vpc_id
    private_subnet_ids         = module.vpc.private_subnet_ids
    database_subnet_ids        = module.vpc.database_subnet_ids
    ecs_cluster_id            = module.ecs.cluster_id
    ecs_service_name          = module.ecs.service_name
    service_discovery_endpoint = module.ecs.service_discovery_endpoint
  }
  sensitive = false
}