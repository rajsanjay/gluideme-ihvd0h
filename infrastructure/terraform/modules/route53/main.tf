# AWS Route 53 DNS configuration for Transfer Requirements Management System
# Implements secure DNS management with DNSSEC, health checks, and query logging
# Provider version: hashicorp/aws ~> 4.0

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
  }
}

# Primary hosted zone for the domain
resource "aws_route53_zone" "main" {
  name    = var.domain_name
  comment = "Managed hosted zone for ${var.environment} environment"

  # Enable DNSSEC if specified
  dynamic "dnssec_config" {
    for_each = var.enable_dnssec ? [1] : []
    content {
      signing_status = "SIGNING"
    }
  }

  tags = {
    Environment = var.environment
    ManagedBy   = "terraform"
    Name        = "${var.domain_name}-zone"
    Purpose     = "DNS management for Transfer Requirements System"
  }
}

# A record for IPv4 CloudFront distribution
resource "aws_route53_record" "cloudfront_ipv4" {
  zone_id = aws_route53_zone.main.zone_id
  name    = var.domain_name
  type    = "A"

  alias {
    name                   = cloudfront_outputs.distribution_domain_name
    zone_id               = cloudfront_outputs.distribution_hosted_zone_id
    evaluate_target_health = true
  }
}

# AAAA record for IPv6 CloudFront distribution
resource "aws_route53_record" "cloudfront_ipv6" {
  zone_id = aws_route53_zone.main.zone_id
  name    = var.domain_name
  type    = "AAAA"

  alias {
    name                   = cloudfront_outputs.distribution_domain_name
    zone_id               = cloudfront_outputs.distribution_hosted_zone_id
    evaluate_target_health = true
  }
}

# CAA records for certificate validation
resource "aws_route53_record" "caa" {
  zone_id = aws_route53_zone.main.zone_id
  name    = var.domain_name
  type    = "CAA"
  ttl     = 300

  records = [
    "0 issue \"amazon.com\"",
    "0 issuewild \"amazon.com\""
  ]
}

# Health check for application endpoint
resource "aws_route53_health_check" "main" {
  count = var.health_check_enabled ? 1 : 0

  fqdn              = var.domain_name
  port              = 443
  type              = "HTTPS"
  resource_path     = var.health_check_path
  failure_threshold = 3
  request_interval  = 30

  regions = [
    "us-west-1",
    "us-east-1",
    "eu-west-1"
  ]

  tags = {
    Name        = "${var.domain_name}-health-check"
    Environment = var.environment
    ManagedBy   = "terraform"
    Purpose     = "Application health monitoring"
  }
}

# CloudWatch Log Group for DNS query logging
resource "aws_cloudwatch_log_group" "dns_logs" {
  count = var.enable_query_logging ? 1 : 0

  name              = "/aws/route53/${var.domain_name}/queries"
  retention_in_days = 30

  tags = {
    Name        = "${var.domain_name}-dns-logs"
    Environment = var.environment
    ManagedBy   = "terraform"
    Purpose     = "DNS query logging"
  }
}

# DNS query logging configuration
resource "aws_route53_query_log" "main" {
  count = var.enable_query_logging ? 1 : 0

  depends_on = [aws_cloudwatch_log_group.dns_logs]

  zone_id                  = aws_route53_zone.main.zone_id
  cloudwatch_log_group_arn = aws_cloudwatch_log_group.dns_logs[0].arn
}

# IAM role for Route 53 query logging
resource "aws_iam_role" "dns_query_logging" {
  count = var.enable_query_logging ? 1 : 0

  name = "route53-query-logging-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "route53.amazonaws.com"
        }
      }
    ]
  })

  inline_policy {
    name = "route53-query-logging-policy"
    policy = jsonencode({
      Version = "2012-10-17"
      Statement = [
        {
          Effect = "Allow"
          Action = [
            "logs:CreateLogStream",
            "logs:PutLogEvents"
          ]
          Resource = "${aws_cloudwatch_log_group.dns_logs[0].arn}:*"
        }
      ]
    })
  }
}

# Outputs for use in other modules
output "zone_id" {
  description = "ID of the Route 53 hosted zone"
  value       = aws_route53_zone.main.zone_id
}

output "domain_name" {
  description = "Domain name managed by Route 53"
  value       = var.domain_name
}

output "name_servers" {
  description = "Name servers for the hosted zone"
  value       = aws_route53_zone.main.name_servers
}

output "health_check_id" {
  description = "ID of the Route 53 health check"
  value       = var.health_check_enabled ? aws_route53_health_check.main[0].id : null
}