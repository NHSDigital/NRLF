data "aws_availability_zones" "available" {}

#------------------------------------------------------------------------------
# VPC
#------------------------------------------------------------------------------

resource "aws_vpc" "rds-cluster-vpc-mgmt" {
  cidr_block           = var.vpc_cidr_block
  instance_tenancy     = "default"
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name        = "${local.project}-rds-cluster-vpc-${local.environment}"
    Environment = local.environment
  }
}

#------------------------------------------------------------------------------
# Subnets
#------------------------------------------------------------------------------

resource "aws_subnet" "private_subnet-mgmt" {
  count             = var.subnet_count.private
  vpc_id            = aws_vpc.rds-cluster-vpc-mgmt.id
  cidr_block        = element(var.private_subnet_cidr_blocks, count.index)
  availability_zone = element(data.aws_availability_zones.available.names, count.index)

  tags = {
    Name        = "${local.project}-private-subnet-${count.index}-${local.environment}"
    Environment = local.environment
    Tier        = "private"
  }
}


resource "aws_db_subnet_group" "rds-cluster-subnet-group" {
  name       = "${local.project}-private-subnet-group-${local.environment}"
  subnet_ids = aws_subnet.private_subnet-mgmt.*.id

  tags = {
    Name = "${local.project}-private-subnet-group-${local.environment}"
  }
}


#------------------------------------------------------------------------------
# Route Table
#------------------------------------------------------------------------------

resource "aws_route_table" "private_route_table-mgmt" {
  vpc_id = aws_vpc.rds-cluster-vpc-mgmt.id
}

resource "aws_route_table_association" "private-mgmt" {
  count          = var.subnet_count.private
  subnet_id      = element(aws_subnet.private_subnet-mgmt, count.index).id
  route_table_id = aws_route_table.private_route_table-mgmt.id
}

#------------------------------------------------------------------------------
# Security Group
#------------------------------------------------------------------------------

resource "aws_security_group" "rds-cluster-vpc-sg" {
  name        = "${local.project}-rds-cluster-sg-${local.environment}"
  description = "Security group for ${local.project}-rds-cluster-vpc"
  vpc_id      = aws_vpc.rds-cluster-vpc-mgmt.id

  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "TCP"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "TCP"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "${local.project}-rds-cluster-sg-${local.environment}"
    Environment = local.environment
  }
}
