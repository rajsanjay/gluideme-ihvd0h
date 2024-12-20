# AWS Provider Configuration v5.0
# Primary and DR region setup for Transfer Requirements Management System

# Primary AWS Provider - US West (Oregon)
provider "aws" {
  region = "us-west-2"
  allowed_account_ids = [var.aws_account_id]

  default_tags {
    tags = {
      Project             = "TRMS"
      Environment         = terraform.workspace
      ManagedBy          = "Terraform"
      Application        = "TransferRequirements"
      CostCenter         = "Engineering"
      DataClassification = "Sensitive"
    }
  }
}

# Secondary AWS Provider for Disaster Recovery - US East (N. Virginia)
provider "aws" {
  alias  = "dr"
  region = "us-east-1"
  allowed_account_ids = [var.aws_account_id]

  default_tags {
    tags = {
      Project             = "TRMS"
      Environment         = "${terraform.workspace}-dr"
      ManagedBy          = "Terraform"
      Application        = "TransferRequirements"
      CostCenter         = "Engineering"
      DataClassification = "Sensitive"
    }
  }
}

# Required Variables
variable "aws_account_id" {
  description = "AWS Account ID where resources will be provisioned"
  type        = string
  sensitive   = true

  validation {
    condition     = can(regex("^\\d{12}$", var.aws_account_id))
    error_message = "AWS Account ID must be a 12-digit number."
  }
}