# Core Terraform functionality for output definitions
terraform {
  required_version = "~> 1.5"
}

# VPC identifier for resource association
output "vpc_id" {
  description = "ID of the created VPC for resource association"
  value       = aws_vpc.main.id
  sensitive   = false
}

# VPC CIDR block marked as sensitive for security
output "vpc_cidr" {
  description = "CIDR block of the created VPC for network planning"
  value       = aws_vpc.main.cidr_block
  sensitive   = true # Marked sensitive to protect network information
}

# Private subnet IDs for application tier resources
output "private_subnet_ids" {
  description = "List of private subnet IDs for application layer deployment"
  value       = aws_subnet.private[*].id
  sensitive   = false
}

# Database subnet IDs for data tier resources
output "database_subnet_ids" {
  description = "List of database subnet IDs for RDS deployment"
  value       = aws_subnet.database[*].id
  sensitive   = false
}

# Private subnet CIDRs marked as sensitive
output "private_subnet_cidrs" {
  description = "List of private subnet CIDR blocks for network planning"
  value       = aws_subnet.private[*].cidr_block
  sensitive   = true # Marked sensitive to protect network topology
}

# Database subnet CIDRs marked as sensitive
output "database_subnet_cidrs" {
  description = "List of database subnet CIDR blocks for network planning"
  value       = aws_subnet.database[*].cidr_block
  sensitive   = true # Marked sensitive to protect database tier network topology
}

# Availability zones used by VPC subnets
output "availability_zones" {
  description = "List of availability zones used by VPC subnets"
  value       = distinct(concat(
    aws_subnet.private[*].availability_zone,
    aws_subnet.database[*].availability_zone
  ))
  sensitive = false
}