# Redis Cluster Connection Details
# Used by application services for cache layer integration
# AWS Provider Version: ~> 5.0

output "redis_primary_endpoint" {
  description = "Primary endpoint address for Redis cluster write operations, used for cache updates and data modifications"
  value       = aws_elasticache_replication_group.main.primary_endpoint_address
}

output "redis_reader_endpoint" {
  description = "Reader endpoint address for Redis cluster read operations, optimized for high-throughput cache reads"
  value       = aws_elasticache_replication_group.main.reader_endpoint_address
}

output "redis_port" {
  description = "Port number for Redis cluster connections, used for both read and write operations"
  value       = aws_elasticache_replication_group.main.port
}

output "redis_security_group_id" {
  description = "ID of the security group controlling Redis cluster access, used for network security configuration"
  value       = aws_security_group.redis.id
}