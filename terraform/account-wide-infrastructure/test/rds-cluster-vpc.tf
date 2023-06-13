data "aws_availability_zones" "available" {}

#------------------------------------------------------------------------------
# VPC
#------------------------------------------------------------------------------

resource "aws_vpc" "rds-cluster-vpc-ref" {
  cidr_block           = var.vpc_cidr_block
  instance_tenancy     = "default"
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name        = "nhsd-nrlf-rds-cluster-vpc-ref"
    Environment = "ref"
  }
}

resource "aws_vpc" "rds-cluster-vpc-int" {
  cidr_block           = var.vpc_cidr_block
  instance_tenancy     = "default"
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name        = "nhsd-nrlf-rds-cluster-vpc-int"
    Environment = "int"
  }
}

#------------------------------------------------------------------------------
# Subnets
#------------------------------------------------------------------------------

resource "aws_subnet" "private-subnet-ref" {
  count             = var.subnet_count.private
  vpc_id            = aws_vpc.rds-cluster-vpc-ref.id
  cidr_block        = element(var.private_subnet_cidr_blocks, count.index)
  availability_zone = element(data.aws_availability_zones.available.names, count.index)

  tags = {
    Name        = "nhsd-nrlf-private-subnet-${count.index}-ref"
    Environment = "ref"
    Tier        = "private"
  }
}


resource "aws_db_subnet_group" "rds-cluster-subnet-group-ref" {
  name       = "nhsd-nrlf-private-subnet-group-ref"
  subnet_ids = aws_subnet.private-subnet-ref.*.id

  tags = {
    Name = "nhsd-nrlf-private-subnet-group-ref"
  }
}

resource "aws_subnet" "private-subnet-int" {
  count             = var.subnet_count.private
  vpc_id            = aws_vpc.rds-cluster-vpc-int.id
  cidr_block        = element(var.private_subnet_cidr_blocks, count.index)
  availability_zone = element(data.aws_availability_zones.available.names, count.index)

  tags = {
    Name        = "nhsd-nrlf-private-subnet-${count.index}-int"
    Environment = "int"
    Tier        = "private"
  }
}


resource "aws_db_subnet_group" "rds-cluster-subnet-group-int" {
  name       = "nhsd-nrlf-private-subnet-group-int"
  subnet_ids = aws_subnet.private-subnet-int.*.id

  tags = {
    Name = "nhsd-nrlf-private-subnet-group-int"
  }
}


#------------------------------------------------------------------------------
# Route Table
#------------------------------------------------------------------------------

resource "aws_route_table" "private-route-table-ref" {
  vpc_id = aws_vpc.rds-cluster-vpc-ref.id
}

resource "aws_route_table_association" "private-ref" {
  count          = var.subnet_count.private
  subnet_id      = element(aws_subnet.private-subnet-ref, count.index).id
  route_table_id = aws_route_table.private-route-table-ref.id
}

resource "aws_route_table" "private-route-table-int" {
  vpc_id = aws_vpc.rds-cluster-vpc-int.id
}

resource "aws_route_table_association" "private-int" {
  count          = var.subnet_count.private
  subnet_id      = element(aws_subnet.private-subnet-int, count.index).id
  route_table_id = aws_route_table.private-route-table-int.id
}
