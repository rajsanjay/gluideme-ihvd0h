# AWS KMS encryption keys configuration for Transfer Requirements Management System
# Implements comprehensive encryption strategy with support for multi-region deployment,
# key rotation, and compliance requirements

# AWS Provider version constraint
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
  }
}

# KMS key for database encryption (RDS)
# Handles encryption of sensitive student records and transfer requirements
resource "aws_kms_key" "database" {
  description             = "KMS key for database encryption - Handles sensitive student records and transfer requirements"
  deletion_window_in_days = var.key_deletion_window
  enable_key_rotation     = var.enable_key_rotation
  multi_region           = var.multi_region

  tags = merge(
    var.tags,
    {
      Name               = "${var.key_prefix}-database-${var.environment}"
      SecurityLevel      = "High"
      DataClassification = "Sensitive"
    }
  )
}

# KMS key for storage encryption (S3)
# Protects uploaded documents and transfer agreements
resource "aws_kms_key" "storage" {
  description             = "KMS key for document storage encryption - Protects uploaded documents and transfer agreements"
  deletion_window_in_days = var.key_deletion_window
  enable_key_rotation     = var.enable_key_rotation
  multi_region           = var.multi_region

  tags = merge(
    var.tags,
    {
      Name               = "${var.key_prefix}-storage-${var.environment}"
      SecurityLevel      = "High"
      DataClassification = "Sensitive"
    }
  )
}

# KMS key for application-level field encryption
# Secures PII and sensitive student data
resource "aws_kms_key" "application" {
  description             = "KMS key for application-level field encryption - Secures PII and sensitive student data"
  deletion_window_in_days = var.key_deletion_window
  enable_key_rotation     = var.enable_key_rotation
  multi_region           = var.multi_region

  tags = merge(
    var.tags,
    {
      Name               = "${var.key_prefix}-application-${var.environment}"
      SecurityLevel      = "High"
      DataClassification = "HighlySensitive"
    }
  )
}

# Alias for database encryption key
resource "aws_kms_alias" "database" {
  name          = "alias/${var.key_prefix}-database-${var.environment}"
  target_key_id = aws_kms_key.database.id
}

# Alias for storage encryption key
resource "aws_kms_alias" "storage" {
  name          = "alias/${var.key_prefix}-storage-${var.environment}"
  target_key_id = aws_kms_key.storage.id
}

# Alias for application encryption key
resource "aws_kms_alias" "application" {
  name          = "alias/${var.key_prefix}-application-${var.environment}"
  target_key_id = aws_kms_key.application.id
}

# Output the database encryption key details
output "database_key" {
  value = {
    id  = aws_kms_key.database.id
    arn = aws_kms_key.database.arn
  }
  description = "Database encryption key details for RDS encryption"
}

# Output the storage encryption key details
output "storage_key" {
  value = {
    id  = aws_kms_key.storage.id
    arn = aws_kms_key.storage.arn
  }
  description = "Storage encryption key details for S3 bucket encryption"
}

# Output the application encryption key details
output "application_key" {
  value = {
    id  = aws_kms_key.application.id
    arn = aws_kms_key.application.arn
  }
  description = "Application encryption key details for field-level encryption"
}