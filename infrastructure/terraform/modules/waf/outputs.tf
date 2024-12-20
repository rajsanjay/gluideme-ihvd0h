# Output definitions for WAF Web ACL resources
# These outputs enable integration with load balancers, API gateways, and monitoring systems

output "web_acl_id" {
  description = "ID of the WAF Web ACL for associating with AWS resources"
  value       = aws_wafv2_web_acl.main.id
}

output "web_acl_arn" {
  description = "ARN of the WAF Web ACL for CloudWatch logging and monitoring"
  value       = aws_wafv2_web_acl.main.arn
}

output "web_acl_capacity" {
  description = "Web ACL capacity units (WCU) used by this Web ACL"
  value       = aws_wafv2_web_acl.main.capacity
}

output "web_acl_name" {
  description = "Name of the WAF Web ACL for reference in monitoring and alerts"
  value       = aws_wafv2_web_acl.main.name
}