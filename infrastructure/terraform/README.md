# Transfer Requirements Management System - Infrastructure Documentation

## Table of Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Module Structure](#module-structure)
- [Environment Configuration](#environment-configuration)
- [Deployment Instructions](#deployment-instructions)
- [Security Considerations](#security-considerations)
- [Monitoring Setup](#monitoring-setup)

## Overview

This repository contains the complete Terraform infrastructure configuration for the Transfer Requirements Management System. The infrastructure is designed for high availability, scalability, and security, following AWS best practices.

### Architecture Diagram

```
Production Environment
┌────────────────────────────────────────┐
│ AWS Cloud - Primary Region (us-west-2) │
│ ┌──────────────┐    ┌──────────────┐  │
│ │   Route 53   │──┬─│  CloudFront  │  │
│ └──────────────┘  │ └──────────────┘  │
│                   │ ┌──────────────┐  │
│                   └─│     WAF      │  │
│                     └──────────────┘  │
│ ┌──────────────────────────────────┐  │
│ │            VPC                   │  │
│ │ ┌────────┐  ┌────────┐  ┌─────┐ │  │
│ │ │Public  │  │Private │  │ DB  │ │  │
│ │ │Subnet  │  │Subnet  │  │Subnet│ │  │
│ │ └────────┘  └────────┘  └─────┘ │  │
│ └──────────────────────────────────┘  │
└────────────────────────────────────────┘
```

## Prerequisites

### Required Software
- Terraform >= 1.5.0
- AWS CLI >= 2.0.0
- Git >= 2.0.0

### AWS Account Requirements
- Administrative access or appropriate IAM permissions
- Access to required AWS services:
  - VPC
  - ECS
  - RDS
  - ElastiCache
  - S3
  - CloudFront
  - Route 53
  - Certificate Manager
  - CloudWatch
  - WAF

### Authentication Setup
```bash
export AWS_ACCESS_KEY_ID="your_access_key"
export AWS_SECRET_ACCESS_KEY="your_secret_key"
export AWS_DEFAULT_REGION="us-west-2"
```

## Module Structure

### Core Modules

#### VPC Module
```hcl
module "vpc" {
  source = "./modules/vpc"
  
  cidr_block         = "10.0.0.0/16"
  availability_zones = ["us-west-2a", "us-west-2b", "us-west-2c"]
  environment        = var.environment
  enable_nat_gateway = true
  enable_vpn_gateway = false
}
```

#### ECS Module
```hcl
module "ecs" {
  source = "./modules/ecs"
  
  cluster_name     = "trms-${var.environment}"
  desired_count    = 4
  cpu_threshold    = 70
  memory_threshold = 80
  container_insights = true
}
```

#### RDS Module
```hcl
module "rds" {
  source = "./modules/rds"
  
  instance_class    = "r6g.xlarge"
  backup_retention  = 30
  multi_az         = true
  storage_encrypted = true
  performance_insights_enabled = true
}
```

## Environment Configuration

### Staging Environment
```hcl
# environments/staging/main.tf
module "staging" {
  source = "../../modules"
  
  environment         = "staging"
  instance_size      = "small"
  multi_az           = false
  backup_retention   = 7
}
```

### Production Environment
```hcl
# environments/prod/main.tf
module "production" {
  source = "../../modules"
  
  environment         = "prod"
  instance_size      = "large"
  multi_az           = true
  backup_retention   = 30
  dr_region          = "us-east-1"
}
```

## Deployment Instructions

### Initial Deployment
```bash
# Initialize Terraform
terraform init

# Plan deployment
terraform plan -var-file=environments/prod/terraform.tfvars

# Apply changes
terraform apply -var-file=environments/prod/terraform.tfvars
```

### Update Procedure
1. Update configuration files
2. Run terraform plan to review changes
3. Create change request ticket
4. Schedule maintenance window
5. Apply changes with approval

### Rollback Process
```bash
# Revert to previous state
terraform plan -target=module.target_module -var-file=environments/prod/terraform.tfvars
terraform apply -target=module.target_module -var-file=environments/prod/terraform.tfvars
```

## Security Considerations

### Encryption Configuration
- RDS: Storage encryption enabled using AWS KMS
- S3: Server-side encryption with AWS managed keys
- ElastiCache: Encryption at rest and in transit
- Application data: Field-level encryption for sensitive data

### Network Security
- VPC Flow Logs enabled
- Security groups with minimal required access
- WAF rules for application protection
- Private subnets for database and application tiers

### Compliance
- FERPA compliance through data encryption
- Audit logging enabled
- Regular security patches
- Automated compliance checking

## Monitoring Setup

### CloudWatch Configuration
```hcl
module "monitoring" {
  source = "./modules/monitoring"
  
  alarm_email = "ops@example.com"
  metrics_retention_days = 90
  enable_detailed_monitoring = true
}
```

### Alert Thresholds
| Metric | Warning | Critical | Action |
|--------|----------|-----------|---------|
| CPU | 70% | 85% | Auto-scale |
| Memory | 75% | 90% | Alert |
| Disk | 75% | 90% | Expand |
| Error Rate | 1% | 5% | Alert |

### Logging
- CloudWatch Logs retention: 90 days
- VPC Flow Logs enabled
- Application logs with structured JSON format
- Audit logs for security events

## Support and Maintenance

### Common Issues
- Terraform state lock resolution
- AWS resource limits
- Deployment rollback procedures
- Security group updates

### Contact Information
- Infrastructure Team: infra@example.com
- Security Team: security@example.com
- Emergency Contact: oncall@example.com

## License
Copyright © 2023 Transfer Requirements Management System