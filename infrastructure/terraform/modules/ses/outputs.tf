# AWS SES Module Outputs
# Version: 1.5+
# Purpose: Exports essential SES configuration values with security considerations
# Last Updated: 2024

# SES Domain Identity ARN - Required for cross-account access and IAM policies
output "ses_domain_identity_arn" {
  description = <<-EOT
    The ARN of the SES domain identity.
    Used for:
    - IAM policy permissions
    - Cross-account access control
    - Resource-based policies
    Note: Treat as sensitive information.
  EOT
  value       = aws_ses_domain_identity.main.arn
  sensitive   = true
}

# Verified Domain Name
output "ses_domain" {
  description = <<-EOT
    The domain name configured for SES.
    Important:
    - Must be verified before sending emails
    - Check AWS Console for verification status
    - Used for email sender address configuration
  EOT
  value       = aws_ses_domain_identity.main.domain
}

# DKIM Tokens for DNS Configuration
output "ses_dkim_tokens" {
  description = <<-EOT
    DKIM tokens for domain verification and email authentication.
    Implementation:
    - Add as CNAME records to domain DNS
    - Format: <token>._domainkey.<domain>
    - Required for enhanced deliverability
    - Improves email security and authenticity
  EOT
  value       = aws_ses_domain_dkim.main.dkim_tokens
}

# Regional SMTP Endpoint
output "ses_smtp_endpoint" {
  description = <<-EOT
    Regional SMTP endpoint for sending emails.
    Configuration:
    - Uses TLS encryption on port 587
    - Requires SMTP credentials from AWS SES
    - Format: email-smtp.<region>.amazonaws.com
    Security Note: Use with AWS Secrets Manager for SMTP credentials
  EOT
  value       = format("email-smtp.%s.amazonaws.com", data.aws_region.current.name)
}

# Configuration Set Name
output "ses_configuration_set_name" {
  description = <<-EOT
    Name of the SES configuration set for email tracking and monitoring.
    Features:
    - Email sending metrics
    - Bounce and complaint tracking
    - Delivery status monitoring
    - Integration with CloudWatch
  EOT
  value       = aws_ses_configuration_set.main.name
}

# SNS Topic ARN for SES Alerts
output "ses_alert_topic_arn" {
  description = <<-EOT
    ARN of the SNS topic for SES alerts and notifications.
    Used for:
    - Bounce rate alerts
    - Complaint notifications
    - Delivery status updates
    Note: Treat as sensitive information.
  EOT
  value       = aws_sns_topic.alerts.arn
  sensitive   = true
}

# CloudWatch Log Group Name
output "ses_cloudwatch_log_group" {
  description = <<-EOT
    Name of the CloudWatch Log Group for SES event logging.
    Contains:
    - Delivery status logs
    - Bounce and complaint events
    - Email tracking information
    - Security and compliance logs
  EOT
  value       = "/aws/ses/${var.environment}"
}

# Email Identity ARN
output "ses_system_email_identity_arn" {
  description = <<-EOT
    ARN of the system notification email identity.
    Used for:
    - System notifications
    - Automated emails
    - Service alerts
    Note: Treat as sensitive information.
  EOT
  value       = aws_ses_email_identity.system.arn
  sensitive   = true
}