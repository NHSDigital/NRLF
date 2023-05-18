data "aws_availability_zones" "available" {}

#------------------------------------------------------------------------------
# VPC
#------------------------------------------------------------------------------

resource "aws_vpc" "vpc" {
  cidr_block           = var.vpc_cidr_block
  instance_tenancy     = "default"
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name        = "${var.prefix}-VPC"
    Environment = var.environment
  }
}

#------------------------------------------------------------------------------
# Internet Gateway
#------------------------------------------------------------------------------

resource "aws_internet_gateway" "igw" {
  vpc_id = aws_vpc.vpc.id

  tags = {
    Name        = "${var.prefix}-IGW"
    Environment = var.environment
  }
}

#------------------------------------------------------------------------------
# Subnets
#------------------------------------------------------------------------------

resource "aws_subnet" "public_subnet" {
  count                   = var.subnet_count.public
  vpc_id                  = aws_vpc.vpc.id
  cidr_block              = element(var.public_subnet_cidr_blocks, count.index)
  availability_zone       = element(data.aws_availability_zones.available.names, count.index)
  map_public_ip_on_launch = true

  tags = {
    Name        = "${var.prefix}-public-subnet-${count.index}"
    Environment = var.environment
    Tier        = "public"
  }
}

resource "aws_subnet" "private_subnet" {
  count             = var.subnet_count.private
  vpc_id            = aws_vpc.vpc.id
  cidr_block        = element(var.private_subnet_cidr_blocks, count.index)
  availability_zone = element(data.aws_availability_zones.available.names, count.index)

  tags = {
    Name        = "${var.prefix}-private-subnet-${count.index}"
    Environment = var.environment
    Tier        = "private"
  }
}

#------------------------------------------------------------------------------
# Route Table
#------------------------------------------------------------------------------

resource "aws_route_table" "public_route_table" {
  vpc_id = aws_vpc.vpc.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.igw.id
  }

  tags = {
    Name = "${var.prefix}-public-route-table"
  }
}

resource "aws_route_table_association" "public" {
  count          = var.subnet_count.public
  subnet_id      = element(aws_subnet.public_subnet, count.index).id
  route_table_id = aws_route_table.public_route_table.id
}

resource "aws_route_table" "private_route_table" {
  vpc_id = aws_vpc.vpc.id
}

resource "aws_route_table_association" "private" {
  count          = var.subnet_count.private
  subnet_id      = element(aws_subnet.private_subnet, count.index).id
  route_table_id = aws_route_table.private_route_table.id
}

#------------------------------------------------------------------------------
# Elastic IP
#------------------------------------------------------------------------------

resource "aws_eip" "eip" {
  count = var.subnet_count.public
  vpc   = true

  tags = {
    Name        = "${var.prefix}-EIP-${count.index}"
    Environment = var.environment
  }
  depends_on = [aws_internet_gateway.igw]
}
