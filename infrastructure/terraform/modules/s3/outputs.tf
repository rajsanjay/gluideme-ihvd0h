# Output configuration for AWS S3 buckets
# Exposes essential bucket properties for integration with other infrastructure components
# while maintaining security best practices and enabling proper IAM/endpoint configuration

# Main bucket identifier
output "bucket_id" {
  description = "The unique identifier of the created S3 bucket, used for direct bucket referencing in other modules"
  value       = aws_s3_bucket.main.id
}

# Main bucket ARN for IAM and KMS policy configuration
output "bucket_arn" {
  description = "The Amazon Resource Name (ARN) of the created S3 bucket, required for IAM policy attachment and KMS key policies"
  value       = aws_s3_bucket.main.arn
}

# Main bucket domain name for endpoint configuration
output "bucket_domain_name" {
  description = "The fully-qualified domain name of the created S3 bucket, used for endpoint configuration and direct bucket access"
  value       = aws_s3_bucket.main.bucket_domain_name
}