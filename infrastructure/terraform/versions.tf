# Terraform version constraint ensuring consistent infrastructure management
# Version 1.5.0+ required for enhanced stability and feature support
terraform {
  required_version = ">= 1.5.0"

  # Required providers block defining cloud provider dependencies
  required_providers {
    # AWS provider configuration for cloud infrastructure management
    # Version ~> 5.0 ensures stable AWS resource provisioning while allowing minor updates
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}