# CloudWatch Log Group outputs with FERPA compliance attributes
output "log_group_arns" {
  description = "List of CloudWatch log group ARNs with FERPA compliance tags"
  value = [
    for log_group in aws_cloudwatch_log_group.component_logs : {
      arn            = log_group.arn
      compliance_tag = log_group.tags["ComplianceScope"]
    }
  ]
}

output "log_group_names" {
  description = "List of CloudWatch log group names for application components"
  value = [
    for log_group in aws_cloudwatch_log_group.component_logs : log_group.name
  ]
}

output "log_group_kms_key_ids" {
  description = "List of KMS key IDs used for FERPA-compliant log encryption"
  value = [
    for log_group in aws_cloudwatch_log_group.component_logs : log_group.kms_key_id
  ]
}

output "log_retention_policies" {
  description = "Map of log retention policies for FERPA compliance requirements"
  value = {
    for name, log_group in aws_cloudwatch_log_group.component_logs : name => {
      retention_days = log_group.retention_in_days
      component     = log_group.tags["Component"]
    }
  }
}

# Metric alarm outputs for transfer requirement monitoring
output "metric_alarm_arns" {
  description = "List of CloudWatch metric alarm ARNs for system monitoring"
  value = concat(
    [for alarm in aws_cloudwatch_metric_alarm.transfer_metrics : alarm.arn],
    [for alarm in aws_cloudwatch_metric_alarm.performance : alarm.arn]
  )
}

output "transfer_processing_alarms" {
  description = "Transfer requirement processing specific alarms and thresholds"
  value = {
    for name, alarm in aws_cloudwatch_metric_alarm.transfer_metrics : name => {
      alarm_name = alarm.alarm_name
      threshold  = alarm.threshold
      metric     = alarm.metric_name
      statistic  = alarm.statistic
    }
  }
}

output "compliance_metric_alarms" {
  description = "FERPA compliance monitoring alarms with tracking metadata"
  value = {
    for name, alarm in aws_cloudwatch_metric_alarm.transfer_metrics : name => {
      alarm_name       = alarm.alarm_name
      compliance_tags  = alarm.tags
      evaluation_time = "${alarm.period * alarm.evaluation_periods}s"
      actions         = alarm.alarm_actions
    }
  }
}

# Dashboard outputs for monitoring visualization
output "dashboard_arns" {
  description = "List of CloudWatch dashboard ARNs for monitoring visualization"
  value = var.dashboard_enabled ? [aws_cloudwatch_dashboard.transfer_system[0].dashboard_arn] : []
}

output "educational_dashboards" {
  description = "Educational metrics specific dashboards and visualization widgets"
  value = var.dashboard_enabled ? {
    dashboard_name = aws_cloudwatch_dashboard.transfer_system[0].dashboard_name
    widgets        = jsondecode(aws_cloudwatch_dashboard.transfer_system[0].dashboard_body).widgets
  } : null
}

# Notification configuration outputs
output "notification_configs" {
  description = "Alert notification configurations and routing rules"
  value = {
    sns_topic_arns = var.notification_endpoints
    routing_rules = {
      for name, alarm in merge(
        aws_cloudwatch_metric_alarm.transfer_metrics,
        aws_cloudwatch_metric_alarm.performance
      ) : name => {
        severity = contains(keys(aws_cloudwatch_metric_alarm.transfer_metrics), name) ? "HIGH" : "MEDIUM"
        actions  = alarm.alarm_actions
      }
    }
  }
}

# Error tracking outputs
output "error_tracking_filters" {
  description = "Log metric filters for error tracking across components"
  value = {
    for name, filter in aws_cloudwatch_log_metric_filter.error_tracking : name => {
      filter_pattern = filter.pattern
      metric_name    = filter.metric_transformation[0].name
      namespace      = filter.metric_transformation[0].namespace
    }
  }
}

# Encryption configuration output
output "log_encryption_config" {
  description = "KMS encryption configuration for FERPA-compliant logging"
  value = {
    kms_key_id            = aws_kms_key.cloudwatch.id
    kms_key_arn          = aws_kms_key.cloudwatch.arn
    rotation_enabled     = aws_kms_key.cloudwatch.enable_key_rotation
    deletion_window_days = aws_kms_key.cloudwatch.deletion_window_in_days
  }
}