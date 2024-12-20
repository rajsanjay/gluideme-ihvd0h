# Route53 outputs configuration for Transfer Requirements Management System
# Exposes essential DNS configuration details for integration with other infrastructure components
# Provider version: hashicorp/terraform ~> 1.5

# Zone ID output for DNS record management and service integration
output "zone_id" {
  description = "The ID of the Route53 hosted zone used for DNS record management and integration with other AWS services like CloudFront and ACM"
  value       = aws_route53_zone.main.zone_id
  # Not marking as sensitive since zone_id is needed for public DNS configuration
}

# Name servers output for domain delegation and DNS configuration
output "name_servers" {
  description = "List of authoritative name servers for the hosted zone required for domain delegation at the registrar level"
  value       = aws_route53_zone.main.name_servers
  # Not marking as sensitive since name servers are required for public DNS resolution
}

# Domain name output for DNS record configuration and service integration
output "domain_name" {
  description = "The fully qualified domain name configured in Route53 used for DNS record creation and service integration"
  value       = aws_route53_zone.main.name
  # Not marking as sensitive since domain name is public information
}

# Health check ID output for monitoring configuration
output "health_check_id" {
  description = "The ID of the Route53 health check used for monitoring application endpoints and DNS failover"
  value       = var.health_check_enabled ? aws_route53_health_check.main[0].id : null
}

# DNS query logging configuration output
output "query_logging_config_id" {
  description = "The ID of the Route53 query logging configuration for DNS monitoring and analysis"
  value       = var.enable_query_logging ? aws_route53_query_log.main[0].id : null
}

# CloudWatch log group ARN for DNS query logs
output "dns_log_group_arn" {
  description = "The ARN of the CloudWatch log group used for DNS query logging"
  value       = var.enable_query_logging ? aws_cloudwatch_log_group.dns_logs[0].arn : null
}

# DNSSEC signing status output
output "dnssec_status" {
  description = "The current status of DNSSEC signing for the hosted zone"
  value       = var.enable_dnssec ? aws_route53_zone.main.dnssec_config[0].signing_status : "DISABLED"
}

# Record set outputs for CloudFront distribution
output "cloudfront_record_names" {
  description = "The record names created for CloudFront distribution access"
  value = {
    ipv4 = try(aws_route53_record.cloudfront_ipv4.name, null)
    ipv6 = try(aws_route53_record.cloudfront_ipv6.name, null)
  }
}

# CAA record details output
output "caa_record_details" {
  description = "Details of the CAA records configured for certificate validation"
  value = {
    name    = try(aws_route53_record.caa.name, null)
    records = try(aws_route53_record.caa.records, [])
  }
}