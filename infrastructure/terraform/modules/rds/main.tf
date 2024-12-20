# AWS Provider configuration with version constraint
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
  }
}

# IAM role for enhanced RDS monitoring
resource "aws_iam_role" "rds_monitoring" {
  name = "${var.project}-${var.environment}-rds-monitoring"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "monitoring.rds.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Environment = var.environment
    Project     = var.project
    ManagedBy   = "terraform"
  }
}

# Attach enhanced monitoring policy to IAM role
resource "aws_iam_role_policy_attachment" "rds_monitoring" {
  role       = aws_iam_role.rds_monitoring.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonRDSEnhancedMonitoringRole"
}

# RDS subnet group for Multi-AZ deployment
resource "aws_db_subnet_group" "main" {
  name        = "${var.project}-${var.environment}-rds"
  subnet_ids  = var.database_subnets
  description = "Database subnet group for ${var.project} ${var.environment} environment"

  tags = {
    Environment = var.environment
    Project     = var.project
    ManagedBy   = "terraform"
  }
}

# Security group for RDS instances
resource "aws_security_group" "rds" {
  name        = "${var.project}-${var.environment}-rds"
  description = "Security group for RDS PostgreSQL instances"
  vpc_id      = var.vpc_id

  # Allow PostgreSQL access from within VPC
  ingress {
    description = "PostgreSQL access from VPC"
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr_block]
  }

  egress {
    description = "Allow all outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Environment = var.environment
    Project     = var.project
    ManagedBy   = "terraform"
  }
}

# Primary RDS instance with Multi-AZ deployment
resource "aws_db_instance" "main" {
  identifier = "${var.project}-${var.environment}"

  # Engine configuration
  engine         = "postgres"
  engine_version = "14.7"
  instance_class = var.instance_class

  # Storage configuration
  allocated_storage     = var.allocated_storage
  max_allocated_storage = 1000  # Enable storage autoscaling
  storage_type         = "gp3"
  storage_encrypted    = true
  kms_key_id          = var.kms_key_id

  # Network configuration
  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.rds.id]
  multi_az              = true
  publicly_accessible   = false

  # Backup configuration
  backup_retention_period = 30
  backup_window          = "03:00-04:00"
  maintenance_window     = "Mon:04:00-Mon:05:00"

  # Performance and monitoring
  performance_insights_enabled          = true
  performance_insights_retention_period = 7
  monitoring_interval                  = 60
  monitoring_role_arn                  = aws_iam_role.rds_monitoring.arn
  enabled_cloudwatch_logs_exports      = ["postgresql", "upgrade"]

  # Security configuration
  deletion_protection = true
  skip_final_snapshot = false
  final_snapshot_identifier = "${var.project}-${var.environment}-final"

  # Auto minor version upgrades
  auto_minor_version_upgrade = true

  tags = {
    Environment = var.environment
    Project     = var.project
    Type        = "Primary"
    ManagedBy   = "terraform"
  }
}

# Read replicas for scaling read operations
resource "aws_db_instance" "replica" {
  count = var.read_replica_count

  identifier = "${var.project}-${var.environment}-replica-${count.index + 1}"

  # Replica configuration
  replicate_source_db = aws_db_instance.main.id
  instance_class     = var.instance_class

  # Network configuration
  vpc_security_group_ids = [aws_security_group.rds.id]
  publicly_accessible   = false

  # Performance and monitoring
  performance_insights_enabled          = true
  performance_insights_retention_period = 7
  monitoring_interval                  = 60
  monitoring_role_arn                  = aws_iam_role.rds_monitoring.arn
  enabled_cloudwatch_logs_exports      = ["postgresql", "upgrade"]

  # Auto minor version upgrades
  auto_minor_version_upgrade = true

  tags = {
    Environment    = var.environment
    Project       = var.project
    Type          = "ReadReplica"
    ReplicaNumber = count.index + 1
    ManagedBy     = "terraform"
  }
}

# CloudWatch alarms for database monitoring
resource "aws_cloudwatch_metric_alarm" "database_cpu" {
  alarm_name          = "${var.project}-${var.environment}-database-cpu"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name        = "CPUUtilization"
  namespace          = "AWS/RDS"
  period             = "300"
  statistic          = "Average"
  threshold          = "80"
  alarm_description  = "This metric monitors database CPU utilization"
  alarm_actions      = var.alarm_actions

  dimensions = {
    DBInstanceIdentifier = aws_db_instance.main.id
  }

  tags = {
    Environment = var.environment
    Project     = var.project
    ManagedBy   = "terraform"
  }
}

# Output the database endpoints
output "primary_endpoint" {
  description = "The endpoint of the primary RDS instance"
  value       = aws_db_instance.main.endpoint
}

output "replica_endpoints" {
  description = "The endpoints of the read replica instances"
  value       = aws_db_instance.replica[*].endpoint
}

output "security_group_id" {
  description = "The ID of the RDS security group"
  value       = aws_security_group.rds.id
}