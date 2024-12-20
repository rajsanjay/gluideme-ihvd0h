# Core Terraform functionality for output definitions
terraform {
  required_version = "~> 1.0"
}

# Primary RDS instance endpoint for database connections
output "primary_endpoint" {
  description = "Primary RDS instance endpoint for database connections in format hostname:port"
  value       = aws_db_instance.main.endpoint
  sensitive   = false
}

# Primary RDS instance ARN for IAM and monitoring
output "primary_arn" {
  description = "Amazon Resource Name (ARN) of the primary RDS instance for IAM and monitoring purposes"
  value       = aws_db_instance.main.arn
  sensitive   = false
}

# Read replica endpoints for read-only connections
output "replica_endpoints" {
  description = "List of read replica endpoints for read-only connections in format hostname:port"
  value       = [for replica in aws_db_instance.replica : replica.endpoint]
  sensitive   = false
}

# Database subnet group name for network configuration
output "db_subnet_group_name" {
  description = "Name of the database subnet group for network configuration and VPC placement"
  value       = aws_db_subnet_group.main.name
  sensitive   = false
}

# Security group ID for database access control
output "security_group_id" {
  description = "ID of the RDS security group controlling database access"
  value       = aws_security_group.rds.id
  sensitive   = false
}

# Primary instance identifier for monitoring
output "instance_identifier" {
  description = "Unique identifier of the primary RDS instance for monitoring and operations"
  value       = aws_db_instance.main.identifier
  sensitive   = false
}

# Database port number
output "port" {
  description = "Port number for PostgreSQL database connections (default: 5432)"
  value       = aws_db_instance.main.port
  sensitive   = false
}

# Master username (sensitive)
output "master_username" {
  description = "Master username for database administrative access (sensitive)"
  value       = aws_db_instance.main.username
  sensitive   = true
}

# PostgreSQL engine version
output "engine_version" {
  description = "PostgreSQL engine version running on the RDS instance"
  value       = aws_db_instance.main.engine_version
  sensitive   = false
}

# Availability zone information
output "availability_zone" {
  description = "Availability zone where the primary RDS instance is deployed"
  value       = aws_db_instance.main.availability_zone
  sensitive   = false
}