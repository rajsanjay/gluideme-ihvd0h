# terraform ~> 1.0

variable "project_name" {
  description = "Name of the project used for resource naming and S3 bucket identification"
  type        = string

  validation {
    condition     = length(var.project_name) > 0 && length(var.project_name) <= 63 && can(regex("^[a-z0-9-]*$", var.project_name))
    error_message = "Project name must be between 1 and 63 characters, contain only lowercase letters, numbers, and hyphens"
  }
}

variable "environment" {
  description = "Deployment environment for resource isolation and security boundaries"
  type        = string

  validation {
    condition     = contains(["staging", "production"], var.environment)
    error_message = "Environment must be either staging or production for security compliance"
  }
}

variable "enable_versioning" {
  description = "Enable versioning for S3 bucket to protect against accidental deletions and maintain data history"
  type        = bool
  default     = true
}

variable "force_destroy" {
  description = "Allow destruction of non-empty bucket - should be false in production for data protection"
  type        = bool
  default     = false
}

variable "lifecycle_glacier_transition_days" {
  description = "Number of days after which objects transition to Glacier storage for cost optimization"
  type        = number
  default     = 90

  validation {
    condition     = var.lifecycle_glacier_transition_days >= 30
    error_message = "Glacier transition must be at least 30 days for operational efficiency"
  }
}

variable "enable_encryption" {
  description = "Enable server-side encryption using AWS KMS for data protection"
  type        = bool
  default     = true
}

variable "kms_key_arn" {
  description = "ARN of KMS key for server-side encryption"
  type        = string
  default     = ""
}

variable "tags" {
  description = "Tags to apply to all resources for cost allocation and resource management"
  type        = map(string)
  default     = {}
}