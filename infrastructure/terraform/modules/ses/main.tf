# AWS SES Module Configuration
# Version: 1.5+
# Purpose: Configures AWS SES for secure email delivery with monitoring and compliance features

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
  }
}

# Data sources for AWS account and region information
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# SES Domain Identity
resource "aws_ses_domain_identity" "main" {
  domain = var.domain_name
  
  tags = merge(var.tags, {
    Name        = "${var.environment}-ses-domain"
    Environment = var.environment
    Service     = "email"
  })
}

# DKIM Configuration for enhanced email security
resource "aws_ses_domain_dkim" "main" {
  domain = aws_ses_domain_identity.main.domain
}

# System notification email identity
resource "aws_ses_email_identity" "system" {
  email = format("no-reply@%s", var.domain_name)
  
  tags = merge(var.tags, {
    Name    = "${var.environment}-system-email"
    Purpose = "system-notifications"
  })
}

# Enhanced Configuration Set with security and monitoring
resource "aws_ses_configuration_set" "main" {
  name                       = format("%s-config-set", var.environment)
  reputation_metrics_enabled = true
  sending_enabled           = true

  delivery_options {
    tls_policy       = "REQUIRE"
    signing_enabled  = true
  }

  tracking_options {
    custom_redirect_domain = var.domain_name
  }

  tags = merge(var.tags, {
    Name      = "${var.environment}-ses-config"
    Component = "email-config"
  })
}

# SNS Topic for SES alerts
resource "aws_sns_topic" "alerts" {
  name = "${var.environment}-ses-alerts"
  
  tags = merge(var.tags, {
    Name    = "${var.environment}-ses-alerts"
    Purpose = "email-monitoring"
  })
}

# CloudWatch Alarms for email monitoring
resource "aws_cloudwatch_metric_alarm" "bounce_rate" {
  alarm_name          = format("%s-ses-bounce-rate", var.environment)
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 5
  metric_name         = "Reputation.BounceRate"
  namespace           = "AWS/SES"
  period             = 300
  statistic          = "Average"
  threshold          = var.alert_threshold
  alarm_description  = "Alert when email bounce rate exceeds threshold"
  alarm_actions      = [aws_sns_topic.alerts.arn]

  dimensions = {
    ConfigurationSet = aws_ses_configuration_set.main.name
  }

  tags = merge(var.tags, {
    Name    = "${var.environment}-bounce-rate-alarm"
    Purpose = "email-monitoring"
  })
}

# CloudWatch Alarm for complaint rate monitoring
resource "aws_cloudwatch_metric_alarm" "complaint_rate" {
  alarm_name          = format("%s-ses-complaint-rate", var.environment)
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 5
  metric_name         = "Reputation.ComplaintRate"
  namespace           = "AWS/SES"
  period             = 300
  statistic          = "Average"
  threshold          = 0.001 # 0.1% complaint rate threshold
  alarm_description  = "Alert when email complaint rate exceeds threshold"
  alarm_actions      = [aws_sns_topic.alerts.arn]

  dimensions = {
    ConfigurationSet = aws_ses_configuration_set.main.name
  }

  tags = merge(var.tags, {
    Name    = "${var.environment}-complaint-rate-alarm"
    Purpose = "email-monitoring"
  })
}

# SES Event Destination for CloudWatch Logs
resource "aws_ses_event_destination" "cloudwatch" {
  name                   = "${var.environment}-cloudwatch-destination"
  configuration_set_name = aws_ses_configuration_set.main.name
  enabled               = true
  matching_types        = ["send", "reject", "bounce", "complaint", "delivery"]

  cloudwatch_destination {
    default_value  = var.environment
    dimension_name = "Environment"
    value_source   = "messageTag"
  }
}

# IAM Role for SES CloudWatch logging
resource "aws_iam_role" "ses_cloudwatch" {
  name = "${var.environment}-ses-cloudwatch-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ses.amazonaws.com"
        }
      }
    ]
  })

  tags = merge(var.tags, {
    Name    = "${var.environment}-ses-cloudwatch-role"
    Purpose = "email-logging"
  })
}

# IAM Policy for SES CloudWatch logging
resource "aws_iam_role_policy" "ses_cloudwatch" {
  name = "${var.environment}-ses-cloudwatch-policy"
  role = aws_iam_role.ses_cloudwatch.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:log-group:/aws/ses/*"
      }
    ]
  })
}