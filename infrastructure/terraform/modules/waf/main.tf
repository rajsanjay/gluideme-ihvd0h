# AWS WAF Module - Version 4.0
# Terraform configuration for AWS WAF with enhanced security rules and monitoring

terraform {
  required_version = "~> 1.5"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
  }
}

# Local variables for resource naming and tagging
locals {
  name_prefix = "${var.environment}-waf"
  common_tags = merge(var.tags, {
    Environment = var.environment
    ManagedBy   = "terraform"
    Service     = "waf"
  })
}

# WAF Web ACL with comprehensive security rules
resource "aws_wafv2_web_acl" "main" {
  name        = "${local.name_prefix}-web-acl"
  description = "WAF rules for protecting web applications with advanced security controls"
  scope       = "REGIONAL"

  default_action {
    allow {
      custom_request_handling {
        insert_header {
          name  = "x-waf-action"
          value = "allowed"
        }
      }
    }
  }

  # Rate-based rule for DDoS protection
  rule {
    name     = "RateBasedProtection"
    priority = 1

    override_action {
      none {}
    }

    statement {
      rate_based_statement {
        limit              = var.rate_limit_threshold
        aggregate_key_type = "IP"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name               = "${local.name_prefix}-rate-based"
      sampled_requests_enabled  = true
    }
  }

  # SQL Injection protection rule
  rule {
    name     = "SQLInjectionProtection"
    priority = 2

    override_action {
      none {}
    }

    statement {
      or_statement {
        statements {
          sql_injection_match_statement {
            field_to_match {
              body {}
            }
            text_transformation {
              priority = 1
              type     = "URL_DECODE"
            }
            text_transformation {
              priority = 2
              type     = "HTML_ENTITY_DECODE"
            }
          }
        }
        statements {
          sql_injection_match_statement {
            field_to_match {
              query_string {}
            }
            text_transformation {
              priority = 1
              type     = "URL_DECODE"
            }
          }
        }
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name               = "${local.name_prefix}-sql-injection"
      sampled_requests_enabled  = true
    }
  }

  # XSS protection rule
  rule {
    name     = "XSSProtection"
    priority = 3

    override_action {
      none {}
    }

    statement {
      xss_match_statement {
        field_to_match {
          body {}
        }
        text_transformation {
          priority = 1
          type     = "NONE"
        }
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name               = "${local.name_prefix}-xss"
      sampled_requests_enabled  = true
    }
  }

  # Geo-blocking rule
  dynamic "rule" {
    for_each = var.block_high_risk_countries ? [1] : []
    content {
      name     = "GeoBlockHighRiskCountries"
      priority = 4

      override_action {
        none {}
      }

      statement {
        geo_match_statement {
          country_codes = var.high_risk_countries
        }
      }

      visibility_config {
        cloudwatch_metrics_enabled = true
        metric_name               = "${local.name_prefix}-geo-block"
        sampled_requests_enabled  = true
      }
    }
  }

  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name               = "${local.name_prefix}-web-acl"
    sampled_requests_enabled  = true
  }

  tags = local.common_tags
}

# CloudWatch Log Group for WAF logs
resource "aws_cloudwatch_log_group" "waf_logs" {
  count             = var.enable_logging ? 1 : 0
  name              = "/aws/waf/${var.environment}"
  retention_in_days = var.log_retention_days
  tags              = local.common_tags
}

# WAF logging configuration
resource "aws_wafv2_web_acl_logging_configuration" "main" {
  count                   = var.enable_logging ? 1 : 0
  log_destination_configs = [aws_cloudwatch_log_group.waf_logs[0].arn]
  resource_arn           = aws_wafv2_web_acl.main.arn

  redacted_fields {
    single_header {
      name = "authorization"
    }
  }

  redacted_fields {
    single_header {
      name = "cookie"
    }
  }

  logging_filter {
    default_behavior = "KEEP"

    filter {
      behavior = "DROP"
      condition {
        action_condition {
          action = "ALLOW"
        }
      }
      requirement = "MEETS_ANY"
    }
  }
}

# CloudWatch metrics for WAF monitoring
resource "aws_cloudwatch_metric_alarm" "waf_blocked_requests" {
  alarm_name          = "${local.name_prefix}-blocked-requests"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "BlockedRequests"
  namespace           = "AWS/WAFV2"
  period             = 300
  statistic          = "Sum"
  threshold          = 100
  alarm_description  = "This metric monitors blocked requests by WAF"
  alarm_actions      = []

  dimensions = {
    WebACL = aws_wafv2_web_acl.main.name
    Region = data.aws_region.current.name
  }

  tags = local.common_tags
}

# Current region data source
data "aws_region" "current" {}

# Outputs for WAF resources
output "web_acl_id" {
  description = "The ID of the WAF Web ACL"
  value       = aws_wafv2_web_acl.main.id
}

output "web_acl_arn" {
  description = "The ARN of the WAF Web ACL"
  value       = aws_wafv2_web_acl.main.arn
}

output "web_acl_capacity" {
  description = "The capacity of the WAF Web ACL"
  value       = aws_wafv2_web_acl.main.capacity
}