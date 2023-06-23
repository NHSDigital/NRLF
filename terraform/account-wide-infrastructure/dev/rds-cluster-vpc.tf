data "aws_availability_zones" "available" {}

#------------------------------------------------------------------------------
# VPC
#------------------------------------------------------------------------------

resource "aws_vpc" "rds-cluster-vpc-dev" {
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

resource "aws_subnet" "private-subnet-dev" {
  count             = var.subnet_count.private
  vpc_id            = aws_vpc.rds-cluster-vpc-dev.id
  cidr_block        = element(var.private_subnet_cidr_blocks, count.index)
  availability_zone = element(data.aws_availability_zones.available.names, count.index)

  tags = {
    Name        = "${local.project}-private-subnet-${count.index}-${local.environment}"
    Environment = local.environment
    Tier        = "private"
  }
}


resource "aws_db_subnet_group" "rds-cluster-subnet-group-dev" {
  name       = "${local.project}-private-subnet-group-${local.environment}"
  subnet_ids = aws_subnet.private-subnet-dev.*.id

  tags = {
    Name = "${local.project}-private-subnet-group-${local.environment}"
  }
}


#------------------------------------------------------------------------------
# Route Table
#------------------------------------------------------------------------------

resource "aws_route_table" "private-route-table-dev" {
  vpc_id = aws_vpc.rds-cluster-vpc-dev.id
}

resource "aws_route_table_association" "private-dev" {
  count          = var.subnet_count.private
  subnet_id      = element(aws_subnet.private-subnet-dev, count.index).id
  route_table_id = aws_route_table.private-route-table-dev.id
}