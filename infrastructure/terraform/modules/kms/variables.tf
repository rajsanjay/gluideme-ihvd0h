# Variables for AWS KMS encryption keys module
# Manages encryption keys for database, storage and application-level encryption
# with comprehensive validation rules and security controls

variable "environment" {
  description = "Environment name for resource naming and tagging (e.g. prod, staging, dev). Must match deployment standards."
  type        = string
  
  validation {
    condition     = can(regex("^(prod|staging|dev)$", var.environment))
    error_message = "Environment must be one of: prod, staging, dev to ensure consistent deployment standards"
  }
}

variable "key_prefix" {
  description = "Prefix for KMS key aliases to ensure consistent naming across resources. Used for key identification and access control."
  type        = string
  default     = "trms"
  
  validation {
    condition     = length(var.key_prefix) > 0 && length(var.key_prefix) <= 20
    error_message = "Key prefix must be between 1 and 20 characters to maintain naming standards"
  }
}

variable "key_deletion_window" {
  description = "Waiting period in days before KMS key deletion. Longer periods provide safety margin for key recovery."
  type        = number
  default     = 30
  
  validation {
    condition     = var.key_deletion_window >= 7 && var.key_deletion_window <= 30
    error_message = "Key deletion window must be between 7 and 30 days to meet security requirements"
  }
}

variable "enable_key_rotation" {
  description = "Enable automatic key rotation for KMS keys. Required for compliance with security standards."
  type        = bool
  default     = true
}

variable "multi_region" {
  description = "Enable multi-region replication for KMS keys. Required for cross-region disaster recovery."
  type        = bool
  default     = false
}

variable "tags" {
  description = "Additional tags to apply to KMS keys for resource organization and compliance tracking."
  type        = map(string)
  default     = {}
}