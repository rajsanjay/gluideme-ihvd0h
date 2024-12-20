# Cluster Outputs
output "cluster_id" {
  description = "The ID of the ECS cluster for reference by other modules and resources"
  value       = aws_ecs_cluster.main.id
  sensitive   = false
}

output "cluster_arn" {
  description = "The ARN of the ECS cluster for IAM policies and service configurations"
  value       = aws_ecs_cluster.main.arn
  sensitive   = false
}

output "cluster_name" {
  description = "The name of the ECS cluster for service discovery and CloudWatch monitoring"
  value       = aws_ecs_cluster.main.name
  sensitive   = false
}

output "cluster_capacity_providers" {
  description = "List of capacity providers (FARGATE/FARGATE_SPOT) enabled for the cluster"
  value       = aws_ecs_cluster.main.capacity_providers
  sensitive   = false
}

# Service Outputs
output "service_id" {
  description = "The ID of the ECS service for reference by other modules and resources"
  value       = aws_ecs_service.main.id
  sensitive   = false
}

output "service_name" {
  description = "The name of the ECS service for monitoring and auto-scaling configurations"
  value       = aws_ecs_service.main.name
  sensitive   = false
}

output "service_arn" {
  description = "The ARN of the ECS service for IAM policies and CloudWatch monitoring"
  value       = aws_ecs_service.main.arn
  sensitive   = false
}

output "service_desired_count" {
  description = "The desired number of tasks running in the service for scaling monitoring"
  value       = aws_ecs_service.main.desired_count
  sensitive   = false
}