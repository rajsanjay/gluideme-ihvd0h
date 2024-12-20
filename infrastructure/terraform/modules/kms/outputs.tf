# Output configuration for AWS KMS encryption keys
# Exposes key IDs and ARNs for database, storage, and application-level encryption
# Used by other infrastructure modules to configure encrypted services

# Database encryption key outputs
output "database_key_id" {
  description = "ID of the KMS key used for database encryption"
  value       = aws_kms_key.database.id
}

output "database_key_arn" {
  description = "ARN of the KMS key used for database encryption"
  value       = aws_kms_key.database.arn
}

# Storage encryption key outputs
output "storage_key_id" {
  description = "ID of the KMS key used for S3 storage encryption"
  value       = aws_kms_key.storage.id
}

output "storage_key_arn" {
  description = "ARN of the KMS key used for S3 storage encryption"
  value       = aws_kms_key.storage.arn
}

# Application-level field encryption key outputs
output "application_key_id" {
  description = "ID of the KMS key used for application-level field encryption"
  value       = aws_kms_key.application.id
}

output "application_key_arn" {
  description = "ARN of the KMS key used for application-level field encryption"
  value       = aws_kms_key.application.arn
}