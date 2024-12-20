# Backend configuration for Transfer Requirements Management System (TRMS)
# Version: 1.5.0
# Purpose: Defines the Terraform state storage and locking mechanism with support for
# multi-environment deployments, secure state management, and concurrent access control

terraform {
  backend "s3" {
    # Primary state storage configuration
    bucket = "trms-terraform-state"
    key    = "terraform.tfstate"
    region = "us-west-2"

    # State file encryption configuration
    encrypt        = true
    kms_key_id    = "aws/s3"
    sse_algorithm = "aws:kms"

    # Multi-environment workspace configuration
    workspace_key_prefix = "env"

    # State locking configuration
    dynamodb_table = "trms-terraform-locks"

    # Enhanced security features
    versioning      = true
    access_logging  = true

    # Additional security configurations
    force_path_style = false # Use virtual-hosted-style S3 URLs
    skip_metadata_api_check = true # Enhanced security for metadata API access
    skip_region_validation = false # Ensure region validation
    skip_credentials_validation = false # Ensure credentials validation

    # HTTP configuration
    max_retries = 5 # Retry attempts for backend operations
  }
}

# Local backend configuration for development and testing
# Uncomment the following block when working locally
# terraform {
#   backend "local" {
#     path = "terraform.tfstate"
#   }
# }

# Backend configuration validation and documentation
locals {
  backend_validation = {
    environment_workspaces = [
      "development",
      "staging",
      "production",
      "dr"
    ]
    required_features = {
      encryption     = true
      versioning    = true
      locking       = true
      logging       = true
    }
    compliance_notes = "Configured for FERPA compliance with encryption and access controls"
  }
}