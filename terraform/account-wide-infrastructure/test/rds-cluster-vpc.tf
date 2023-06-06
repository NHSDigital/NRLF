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
    Name        = "nhsd-nrlf-rds-cluster-vpc-dev"
    Environment = "dev"
  }
}

#------------------------------------------------------------------------------
# Subnets
#------------------------------------------------------------------------------

resource "aws_subnet" "private_subnet-dev" {
  count             = var.subnet_count.private
  vpc_id            = aws_vpc.rds-cluster-vpc-dev.id
  cidr_block        = element(var.private_subnet_cidr_blocks, count.index)
  availability_zone = element(data.aws_availability_zones.available.names, count.index)

  tags = {
    Name        = "nhsd-nrlf-private-subnet-${count.index}-dev"
    Environment = "dev"
    Tier        = "private"
  }
}


resource "aws_db_subnet_group" "rds-cluster-subnet-group" {
  name       = "nhsd-nrlf-private-subnet-group-dev"
  subnet_ids = aws_subnet.private_subnet-dev.*.id

  tags = {
    Name = "nhsd-nrlf-private-subnet-group-dev"
  }
}


#------------------------------------------------------------------------------
# Route Table
#------------------------------------------------------------------------------

resource "aws_route_table" "private_route_table-dev" {
  vpc_id = aws_vpc.rds-cluster-vpc-dev.id
}

resource "aws_route_table_association" "private-dev" {
  count          = var.subnet_count.private
  subnet_id      = element(aws_subnet.private_subnet-dev, count.index).id
  route_table_id = aws_route_table.private_route_table-dev.id
}
