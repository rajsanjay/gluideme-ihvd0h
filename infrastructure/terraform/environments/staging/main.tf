# Terraform configuration for staging environment
# Implements single-AZ, fixed capacity infrastructure for pre-production testing
# AWS Provider version ~> 5.0

terraform {
  required_version = "~> 1.5"
  
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

  # S3 backend configuration for state management
  backend "s3" {
    bucket         = "trms-terraform-state"
    key            = "staging/terraform.tfstate"
    region         = "us-west-2"
    encrypt        = true
    dynamodb_table = "trms-terraform-locks"
  }
}

# Provider configuration
provider "aws" {
  region = var.aws_region

  default_tags {
    tags = local.common_tags
  }
}

# Local variables
locals {
  environment = "staging"
  project_name = "trms"
  
  # Common tags for resource management
  common_tags = {
    Environment       = "staging"
    Project          = "TRMS"
    ManagedBy        = "Terraform"
    CostCenter       = "PreProduction"
    DataClassification = "Sensitive"
  }

  # VPC Configuration
  vpc_cidr = "10.1.0.0/16"
  azs      = ["${var.aws_region}a"] # Single AZ for staging
  
  private_subnets  = ["10.1.1.0/24"]
  database_subnets = ["10.1.2.0/24"]
}

# KMS module for encryption
module "kms" {
  source = "../../modules/kms"
  
  environment         = local.environment
  key_prefix         = local.project_name
  key_deletion_window = 7
  enable_key_rotation = true
  multi_region       = false
  
  tags = local.common_tags
}

# VPC module with single AZ configuration
module "vpc" {
  source = "../../modules/vpc"
  
  environment           = local.environment
  vpc_cidr             = local.vpc_cidr
  availability_zones   = local.azs
  private_subnet_cidrs = local.private_subnets
  database_subnet_cidrs = local.database_subnets
  
  single_nat_gateway    = true
  enable_flow_logs     = true
  flow_logs_retention  = 7
  
  tags = local.common_tags
}

# ECS module with fixed capacity
module "ecs" {
  source = "../../modules/ecs"
  
  project_name    = local.project_name
  environment     = local.environment
  vpc_id         = module.vpc.vpc_id
  private_subnets = module.vpc.private_subnet_ids
  
  # Fixed capacity configuration for staging
  task_cpu       = 1024
  task_memory    = 2048
  desired_count  = 2
  
  # Container configuration
  container_image = "${local.project_name}-api:staging"
  container_port  = 8000
  health_check_path = "/health"
  
  # Autoscaling thresholds
  cpu_threshold    = 70
  memory_threshold = 80
  
  tags = local.common_tags
}

# RDS module with single-AZ configuration
module "rds" {
  source = "../../modules/rds"
  
  project     = local.project_name
  environment = local.environment
  vpc_id      = module.vpc.vpc_id
  vpc_cidr_block = local.vpc_cidr
  database_subnets = module.vpc.database_subnet_ids
  
  # Single-AZ configuration for staging
  instance_class = "db.r6g.large"
  allocated_storage = 100
  multi_az     = false
  
  # Reduced backup retention for staging
  backup_retention_period = 7
  
  # KMS encryption
  kms_key_id = module.kms.database_key_id
  
  # Monitoring configuration
  monitoring_interval = 60
  alarm_actions     = [] # No alarms for staging
  
  read_replica_count = 0 # No read replicas in staging
  
  tags = local.common_tags
}

# Outputs for other modules or external references
output "vpc_id" {
  description = "ID of the staging VPC"
  value       = module.vpc.vpc_id
}

output "ecs_cluster_name" {
  description = "Name of the ECS cluster"
  value       = module.ecs.cluster_name
}

output "rds_endpoint" {
  description = "RDS instance endpoint"
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