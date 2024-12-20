# AWS CloudWatch Configuration for Transfer Requirements Management System
# Version: ~> 4.16
# Purpose: Implements comprehensive monitoring, logging and alerting with FERPA compliance

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.16"
    }
  }
}

# Local variables for common configurations
locals {
  common_tags = {
    Environment     = var.environment
    Project         = var.project_name
    ManagedBy      = "terraform"
    ComplianceScope = "FERPA"
    DataRetention  = var.log_retention_days
  }

  # Component names for log groups
  log_components = [
    "api",
    "worker",
    "transfer-processor",
    "validation-engine",
    "requirement-parser"
  ]

  # Critical metrics for transfer processing
  transfer_metrics = [
    "RequirementProcessingTime",
    "ValidationAccuracy",
    "TransferPathCompletion",
    "RequirementParsingErrors"
  ]
}

# KMS key for log encryption (FERPA compliance)
resource "aws_kms_key" "cloudwatch" {
  description             = "KMS key for CloudWatch logs encryption"
  deletion_window_in_days = 7
  enable_key_rotation    = true
  
  tags = merge(local.common_tags, {
    Purpose = "LogEncryption"
  })
}

# Log Groups for each component with FERPA-compliant encryption
resource "aws_cloudwatch_log_group" "component_logs" {
  for_each = toset(local.log_components)

  name              = "/trms/${var.environment}/${each.value}"
  retention_in_days = var.log_retention_days
  kms_key_id       = aws_kms_key.cloudwatch.arn

  tags = merge(local.common_tags, {
    Component = each.value
  })
}

# Metric Alarms for transfer processing metrics
resource "aws_cloudwatch_metric_alarm" "transfer_metrics" {
  for_each = {
    processing_time = {
      metric_name = "RequirementProcessingTime"
      threshold   = 24 # 24 hours as per success criteria
      comparison  = "GreaterThanThreshold"
    }
    validation_accuracy = {
      metric_name = "ValidationAccuracy"
      threshold   = 99.99 # 99.99% accuracy requirement
      comparison  = "LessThanThreshold"
    }
    system_availability = {
      metric_name = "SystemAvailability"
      threshold   = 99.9 # 99.9% uptime requirement
      comparison  = "LessThanThreshold"
    }
    error_rate = {
      metric_name = "ErrorRate"
      threshold   = var.alarm_thresholds[var.environment].error_rate
      comparison  = "GreaterThanThreshold"
    }
  }

  alarm_name          = "TRMS-${var.environment}-${each.key}"
  comparison_operator = each.value.comparison
  evaluation_periods  = 3
  metric_name        = each.value.metric_name
  namespace          = var.metric_namespace
  period             = 300
  statistic          = "Average"
  threshold          = each.value.threshold
  alarm_description  = "Alert for ${each.key} in ${var.environment}"
  alarm_actions      = var.notification_endpoints

  tags = merge(local.common_tags, {
    MetricType = each.key
  })
}

# Performance Monitoring Alarms
resource "aws_cloudwatch_metric_alarm" "performance" {
  for_each = {
    api_latency = {
      metric_name = "APILatency"
      threshold   = var.alarm_thresholds[var.environment].api_latency
      comparison  = "GreaterThanThreshold"
    }
    cpu_utilization = {
      metric_name = "CPUUtilization"
      threshold   = var.alarm_thresholds[var.environment].cpu_utilization
      comparison  = "GreaterThanThreshold"
    }
    memory_utilization = {
      metric_name = "MemoryUtilization"
      threshold   = var.alarm_thresholds[var.environment].memory_utilization
      comparison  = "GreaterThanThreshold"
    }
  }

  alarm_name          = "TRMS-${var.environment}-${each.key}"
  comparison_operator = each.value.comparison
  evaluation_periods  = 2
  metric_name        = each.value.metric_name
  namespace          = var.metric_namespace
  period             = 300
  statistic          = "Average"
  threshold          = each.value.threshold
  alarm_description  = "Performance alert for ${each.key} in ${var.environment}"
  alarm_actions      = var.notification_endpoints

  tags = merge(local.common_tags, {
    MetricType = "Performance"
  })
}

# Transfer System Dashboard
resource "aws_cloudwatch_dashboard" "transfer_system" {
  count = var.dashboard_enabled ? 1 : 0

  dashboard_name = "TRMS-${var.environment}-Overview"
  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        width  = 12
        height = 6
        properties = {
          metrics = [
            ["${var.metric_namespace}", "RequirementProcessingTime"],
            ["${var.metric_namespace}", "ValidationAccuracy"],
            ["${var.metric_namespace}", "SystemAvailability"]
          ]
          period = 300
          region = data.aws_region.current.name
          title  = "Transfer System Core Metrics"
        }
      },
      {
        type   = "metric"
        width  = 12
        height = 6
        properties = {
          metrics = [
            ["${var.metric_namespace}", "APILatency"],
            ["${var.metric_namespace}", "CPUUtilization"],
            ["${var.metric_namespace}", "MemoryUtilization"]
          ]
          period = 300
          region = data.aws_region.current.name
          title  = "System Performance Metrics"
        }
      }
    ]
  })
}

# Log Metric Filters for Error Tracking
resource "aws_cloudwatch_log_metric_filter" "error_tracking" {
  for_each = aws_cloudwatch_log_group.component_logs

  name           = "ErrorTracking-${each.key}"
  pattern        = "[timestamp, requestid, level = ERROR, message]"
  log_group_name = each.value.name

  metric_transformation {
    name          = "ErrorCount"
    namespace     = var.metric_namespace
    value         = "1"
    default_value = 0
  }
}

# Data source for current region
data "aws_region" "current" {}

# Outputs for use by other modules
output "log_groups" {
  description = "Map of created CloudWatch log groups"
  value = {
    for k, v in aws_cloudwatch_log_group.component_logs : k => {
      arn        = v.arn
      name       = v.name
      kms_key_id = v.kms_key_id
    }
  }
}

output "transfer_metric_alarms" {
  description = "Map of created transfer metric alarms"
  value = {
    for k, v in aws_cloudwatch_metric_alarm.transfer_metrics : k => {
      arn           = v.arn
      alarm_name    = v.alarm_name
      alarm_actions = v.alarm_actions
    }
  }
}

output "transfer_dashboard" {
  description = "Created CloudWatch dashboard details"
  value = var.dashboard_enabled ? {
    arn            = aws_cloudwatch_dashboard.transfer_system[0].dashboard_arn
    dashboard_name = aws_cloudwatch_dashboard.transfer_system[0].dashboard_name
    dashboard_body = aws_cloudwatch_dashboard.transfer_system[0].dashboard_body
  } : null
}