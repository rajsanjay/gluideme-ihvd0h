# AWS S3 configuration for Transfer Requirements Management System
# Implements secure document storage with enhanced encryption, lifecycle management,
# and comprehensive access controls

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
  }
}

# Main document storage bucket
resource "aws_s3_bucket" "main" {
  bucket = "${var.project_name}-${var.environment}-documents"
  
  # Enable force destroy only in non-production environments
  force_destroy = var.environment != "prod"

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-${var.environment}-documents"
      DataClassification = "Sensitive"
      Environment = var.environment
      Purpose = "Document Storage"
    }
  )
}

# Access logging bucket
resource "aws_s3_bucket" "logs" {
  bucket = "${var.project_name}-${var.environment}-logs"
  
  force_destroy = var.environment != "prod"

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-${var.environment}-logs"
      DataClassification = "Internal"
      Environment = var.environment
      Purpose = "Access Logging"
    }
  )
}

# Enable versioning with MFA delete protection
resource "aws_s3_bucket_versioning" "main" {
  bucket = aws_s3_bucket.main.id
  
  versioning_configuration {
    status = "Enabled"
    mfa_delete = var.environment == "prod" ? "Enabled" : "Disabled"
  }
}

# Configure server-side encryption using KMS
resource "aws_s3_bucket_server_side_encryption_configuration" "main" {
  bucket = aws_s3_bucket.main.id

  rule {
    apply_server_side_encryption_by_default {
      kms_master_key_id = var.storage_key_arn
      sse_algorithm     = "aws:kms"
    }
    bucket_key_enabled = true
  }
}

# Configure lifecycle rules with intelligent tiering
resource "aws_s3_bucket_lifecycle_configuration" "main" {
  bucket = aws_s3_bucket.main.id

  rule {
    id     = "document-lifecycle"
    status = "Enabled"

    # Transition to intelligent tiering after 30 days
    dynamic "transition" {
      for_each = var.enable_intelligent_tiering ? [1] : []
      content {
        days          = 30
        storage_class = "INTELLIGENT_TIERING"
      }
    }

    # Archive old versions to Glacier
    noncurrent_version_transition {
      noncurrent_days = 90
      storage_class   = "GLACIER"
    }

    # Clean up delete markers
    expiration {
      expired_object_delete_marker = true
    }
  }
}

# Enable access logging
resource "aws_s3_bucket_logging" "main" {
  count = var.enable_access_logging ? 1 : 0
  
  bucket = aws_s3_bucket.main.id

  target_bucket = aws_s3_bucket.logs.id
  target_prefix = "s3-access-logs/"
}

# Block public access
resource "aws_s3_bucket_public_access_block" "main" {
  bucket = aws_s3_bucket.main.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Configure CORS for web access
resource "aws_s3_bucket_cors_configuration" "main" {
  bucket = aws_s3_bucket.main.id

  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["GET", "PUT", "POST", "DELETE"]
    allowed_origins = [var.allowed_origin]
    expose_headers  = ["ETag"]
    max_age_seconds = 3000
  }
}

# Bucket policy for secure access
resource "aws_s3_bucket_policy" "main" {
  bucket = aws_s3_bucket.main.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "EnforceSSLOnly"
        Effect    = "Deny"
        Principal = "*"
        Action    = "s3:*"
        Resource = [
          aws_s3_bucket.main.arn,
          "${aws_s3_bucket.main.arn}/*"
        ]
        Condition = {
          Bool = {
            "aws:SecureTransport" = "false"
          }
        }
      },
      {
        Sid       = "EnforceEncryptionInTransit"
        Effect    = "Deny"
        Principal = "*"
        Action    = "s3:PutObject"
        Resource  = "${aws_s3_bucket.main.arn}/*"
        Condition = {
          StringNotEquals = {
            "s3:x-amz-server-side-encryption" = "aws:kms"
          }
        }
      }
    ]
  })
}

# Output bucket details
output "bucket_id" {
  description = "ID of the created S3 bucket"
  value       = aws_s3_bucket.main.id
}

output "bucket_arn" {
  description = "ARN of the created S3 bucket"
  value       = aws_s3_bucket.main.arn
}

output "bucket_domain_name" {
  description = "Domain name of the bucket for DNS configuration"
  value       = aws_s3_bucket.main.bucket_domain_name
}