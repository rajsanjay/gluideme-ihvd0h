# AWS Provider configuration with enhanced security features
terraform {
  required_version = "~> 1.5"

  # S3 backend configuration with encryption and versioning
  backend "s3" {
    bucket         = "trms-terraform-state-prod"
    key            = "prod/terraform.tfstate"
    region         = "us-west-2"
    encrypt        = true
    dynamodb_table = "trms-terraform-locks"
    
    # Enhanced backend security settings
    kms_key_id     = "alias/terraform-bucket-key"
    acl            = "private"
    versioning     = true
  }

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.5"
    }
  }
}

# AWS Provider configuration with assume role for enhanced security
provider "aws" {
  region = var.aws_region

  # Enhanced security with assume role
  assume_role {
    role_arn = "arn:aws:iam::${var.aws_account_id}:role/TerraformDeploymentRole"
  }

  default_tags {
    tags = local.common_tags
  }
}

# Local variables for resource naming and tagging
locals {
  common_tags = {
    Environment         = "prod"
    Project            = "TRMS"
    ManagedBy          = "Terraform"
    DataClassification = "FERPA-Sensitive"
    ComplianceScope    = "FERPA"
    BackupRetention    = "7-Years"
    CostCenter         = "Academic-IT"
  }

  # Enhanced naming convention for resources
  name_prefix = "trms-prod"
}

# VPC Module with enhanced security and monitoring
module "vpc" {
  source = "../../modules/vpc"

  environment         = "prod"
  vpc_cidr           = "10.0.0.0/16"
  availability_zones = ["us-west-2a", "us-west-2b", "us-west-2c"]
  
  # Subnet configuration with strict isolation
  private_subnet_cidrs  = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  database_subnet_cidrs = ["10.0.4.0/24", "10.0.5.0/24", "10.0.6.0/24"]
  
  # Enhanced network security features
  enable_flow_logs     = true
  flow_logs_retention  = 365  # 1 year retention for compliance
  enable_network_acls  = true
  single_nat_gateway   = false  # High availability with multiple NAT gateways

  tags = local.common_tags
}

# KMS Module for encryption key management
module "kms" {
  source = "../../modules/kms"

  environment          = "prod"
  key_prefix          = "trms"
  key_deletion_window = 30
  enable_key_rotation = true
  multi_region        = true  # Enable for cross-region DR
  
  tags = local.common_tags
}

# ECS Module with enhanced monitoring and auto-scaling
module "ecs" {
  source = "../../modules/ecs"

  project_name = "trms"
  environment  = "prod"
  vpc_id       = module.vpc.vpc_id
  private_subnets = module.vpc.private_subnet_ids

  # Container configuration
  task_cpu       = 2048
  task_memory    = 4096
  desired_count  = 4
  
  # Auto-scaling configuration
  cpu_threshold    = 70
  memory_threshold = 80
  
  # Enhanced monitoring
  enable_container_insights = true
  monitoring_interval      = 60

  # Container security
  container_port     = 8000
  health_check_path  = "/health"
  
  tags = local.common_tags
}

# RDS Module with enhanced security and monitoring
module "rds" {
  source = "../../modules/rds"

  project     = "trms"
  environment = "prod"
  vpc_id      = module.vpc.vpc_id
  
  # Network configuration
  database_subnets = module.vpc.database_subnet_ids
  vpc_cidr_block   = module.vpc.vpc_cidr
  
  # Instance configuration
  instance_class      = "db.r6g.xlarge"
  allocated_storage   = 100
  read_replica_count  = 2
  
  # Enhanced security configuration
  kms_key_id = module.kms.database_key_id
  
  # Monitoring configuration
  alarm_actions = ["arn:aws:sns:${var.aws_region}:${var.aws_account_id}:DatabaseAlerts"]
  
  tags = local.common_tags
}

# CloudWatch Log Groups for centralized logging
resource "aws_cloudwatch_log_group" "application" {
  name              = "/aws/application/${local.name_prefix}"
  retention_in_days = 365
  kms_key_id        = module.kms.application_key_arn

  tags = merge(
    local.common_tags,
    {
      Name = "${local.name_prefix}-application-logs"
    }
  )
}

# S3 Bucket for application storage with encryption
resource "aws_s3_bucket" "application_storage" {
  bucket = "${local.name_prefix}-storage"

  tags = merge(
    local.common_tags,
    {
      Name = "${local.name_prefix}-storage"
    }
  )
}

resource "aws_s3_bucket_server_side_encryption_configuration" "application_storage" {
  bucket = aws_s3_bucket.application_storage.id

  rule {
    apply_server_side_encryption_by_default {
      kms_master_key_id = module.kms.storage_key_id
      sse_algorithm     = "aws:kms"
    }
  }
}

# Outputs for other modules and documentation
output "vpc_id" {
  description = "ID of the production VPC"
  value       = module.vpc.vpc_id
}

output "ecs_cluster_name" {
  description = "Name of the production ECS cluster"
  value       = module.ecs.cluster_name
}

output "rds_endpoint" {
  description = "Endpoint of the production RDS instance"
  value       = module.rds.primary_endpoint
  sensitive   = true
}

output "kms_keys" {
  description = "KMS key ARNs for encryption"
  value = {
    database    = module.kms.database_key_arn
    storage     = module.kms.storage_key_arn
    application = module.kms.application_key_arn
  }
  sensitive = true
}