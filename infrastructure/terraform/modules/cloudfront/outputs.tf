# CloudFront distribution outputs for Transfer Requirements Management System
# Exposes essential distribution details for DNS configuration and security integration
# Provider version: hashicorp/terraform ~> 1.5

# Distribution ID output for Route53 and WAF configurations
output "distribution_id" {
  description = "ID of the CloudFront distribution for use in Route53 and WAF configurations"
  value       = aws_cloudfront_distribution.main.id
}

# Distribution domain name for DNS configuration
output "distribution_domain_name" {
  description = "Domain name of the CloudFront distribution for DNS configuration in Route53"
  value       = aws_cloudfront_distribution.main.domain_name
}

# Distribution hosted zone ID for Route53 alias records
output "distribution_hosted_zone_id" {
  description = "Route53 hosted zone ID of the CloudFront distribution for alias record configuration"
  value       = aws_cloudfront_distribution.main.hosted_zone_id
}