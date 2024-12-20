# AWS Provider configuration with version constraint
# AWS Provider version ~> 5.0
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# Data source for available AWS Availability Zones
data "aws_availability_zones" "available" {
  state = "available"
  filter {
    name   = "opt-in-status"
    values = ["opt-in-not-required"]
  }
}

# Main VPC resource with enhanced networking features
resource "aws_vpc" "main" {
  cidr_block                           = var.vpc_cidr
  enable_dns_hostnames                 = true
  enable_dns_support                   = true
  enable_network_address_usage_metrics = true

  tags = merge(
    {
      Name                = "${var.environment}-vpc"
      Environment        = var.environment
      SecurityZone       = "restricted"
      NetworkTier        = "core"
      MonitoringEnabled  = "true"
      CreatedBy         = "terraform"
    },
    var.tags
  )
}

# Internet Gateway for public subnet connectivity
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = merge(
    {
      Name        = "${var.environment}-igw"
      Environment = var.environment
    },
    var.tags
  )
}

# Private subnets for application layer
resource "aws_subnet" "private" {
  count             = length(var.availability_zones)
  vpc_id            = aws_vpc.main.id
  cidr_block        = var.private_subnet_cidrs[count.index]
  availability_zone = var.availability_zones[count.index]

  tags = merge(
    {
      Name                              = "${var.environment}-private-${var.availability_zones[count.index]}"
      Environment                       = var.environment
      Tier                             = "private"
      "kubernetes.io/role/internal-elb" = "1"
    },
    var.tags
  )
}

# Database subnets with enhanced isolation
resource "aws_subnet" "database" {
  count             = length(var.availability_zones)
  vpc_id            = aws_vpc.main.id
  cidr_block        = var.database_subnet_cidrs[count.index]
  availability_zone = var.availability_zones[count.index]

  tags = merge(
    {
      Name        = "${var.environment}-db-${var.availability_zones[count.index]}"
      Environment = var.environment
      Tier        = "database"
    },
    var.tags
  )
}

# NAT Gateway for private subnet internet access
resource "aws_eip" "nat" {
  count  = var.single_nat_gateway ? 1 : length(var.availability_zones)
  domain = "vpc"

  tags = merge(
    {
      Name        = "${var.environment}-nat-${count.index + 1}"
      Environment = var.environment
    },
    var.tags
  )
}

resource "aws_nat_gateway" "main" {
  count         = var.single_nat_gateway ? 1 : length(var.availability_zones)
  allocation_id = aws_eip.nat[count.index].id
  subnet_id     = aws_subnet.private[count.index].id

  tags = merge(
    {
      Name        = "${var.environment}-nat-${count.index + 1}"
      Environment = var.environment
    },
    var.tags
  )

  depends_on = [aws_internet_gateway.main]
}

# Route tables for private subnets
resource "aws_route_table" "private" {
  count  = length(var.availability_zones)
  vpc_id = aws_vpc.main.id

  tags = merge(
    {
      Name        = "${var.environment}-private-rt-${count.index + 1}"
      Environment = var.environment
      Tier        = "private"
    },
    var.tags
  )
}

# Routes for private subnet internet access via NAT Gateway
resource "aws_route" "private_nat" {
  count                  = length(var.availability_zones)
  route_table_id         = aws_route_table.private[count.index].id
  destination_cidr_block = "0.0.0.0/0"
  nat_gateway_id         = var.single_nat_gateway ? aws_nat_gateway.main[0].id : aws_nat_gateway.main[count.index].id
}

# Route table associations for private subnets
resource "aws_route_table_association" "private" {
  count          = length(var.availability_zones)
  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private[count.index].id
}

# Database subnet route tables with strict isolation
resource "aws_route_table" "database" {
  count  = length(var.availability_zones)
  vpc_id = aws_vpc.main.id

  tags = merge(
    {
      Name        = "${var.environment}-db-rt-${count.index + 1}"
      Environment = var.environment
      Tier        = "database"
    },
    var.tags
  )
}

# Route table associations for database subnets
resource "aws_route_table_association" "database" {
  count          = length(var.availability_zones)
  subnet_id      = aws_subnet.database[count.index].id
  route_table_id = aws_route_table.database[count.index].id
}

# VPC Flow Logs configuration for network monitoring
resource "aws_flow_log" "main" {
  count                = var.enable_flow_logs ? 1 : 0
  vpc_id              = aws_vpc.main.id
  traffic_type        = "ALL"
  log_destination_type = "cloud-watch-logs"
  log_group_name      = "/aws/vpc/${var.environment}-flow-logs"
  retention_in_days   = var.flow_logs_retention

  tags = merge(
    {
      Name        = "${var.environment}-vpc-flow-logs"
      Environment = var.environment
    },
    var.tags
  )
}

# Network ACL for enhanced subnet isolation
resource "aws_network_acl" "private" {
  vpc_id     = aws_vpc.main.id
  subnet_ids = aws_subnet.private[*].id

  ingress {
    protocol   = -1
    rule_no    = 100
    action     = "allow"
    cidr_block = var.vpc_cidr
    from_port  = 0
    to_port    = 0
  }

  egress {
    protocol   = -1
    rule_no    = 100
    action     = "allow"
    cidr_block = "0.0.0.0/0"
    from_port  = 0
    to_port    = 0
  }

  tags = merge(
    {
      Name        = "${var.environment}-private-nacl"
      Environment = var.environment
    },
    var.tags
  )
}

# Network ACL for database subnet isolation
resource "aws_network_acl" "database" {
  vpc_id     = aws_vpc.main.id
  subnet_ids = aws_subnet.database[*].id

  ingress {
    protocol   = -1
    rule_no    = 100
    action     = "allow"
    cidr_block = var.vpc_cidr
    from_port  = 0
    to_port    = 0
  }

  egress {
    protocol   = -1
    rule_no    = 100
    action     = "allow"
    cidr_block = var.vpc_cidr
    from_port  = 0
    to_port    = 0
  }

  tags = merge(
    {
      Name        = "${var.environment}-database-nacl"
      Environment = var.environment
    },
    var.tags
  )
}