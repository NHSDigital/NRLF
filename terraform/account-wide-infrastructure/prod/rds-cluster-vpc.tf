data "aws_availability_zones" "available" {}

#------------------------------------------------------------------------------
# VPC
#------------------------------------------------------------------------------

resource "aws_vpc" "rds-cluster-vpc-prod" {
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

resource "aws_subnet" "private-subnet-prod" {
  count             = var.subnet_count.private
  vpc_id            = aws_vpc.rds-cluster-vpc-prod.id
  cidr_block        = element(var.private_subnet_cidr_blocks, count.index)
  availability_zone = element(data.aws_availability_zones.available.names, count.index)

  tags = {
    Name        = "${local.project}-private-subnet-${count.index}-${local.environment}"
    Environment = local.environment
    Tier        = "private"
  }
}


resource "aws_db_subnet_group" "rds-cluster-subnet-group-prod" {
  name       = "${local.project}-private-subnet-group-${local.environment}"
  subnet_ids = aws_subnet.private-subnet-prod.*.id

  tags = {
    Name = "${local.project}-private-subnet-group-${local.environment}"
  }
}


#------------------------------------------------------------------------------
# Route Table
#------------------------------------------------------------------------------

resource "aws_route_table" "private-route-table-prod" {
  vpc_id = aws_vpc.rds-cluster-vpc-prod.id
}

resource "aws_route_table_association" "private-prod" {
  count          = var.subnet_count.private
  subnet_id      = element(aws_subnet.private-subnet-prod, count.index).id
  route_table_id = aws_route_table.private-route-table-prod.id
}

#------------------------------------------------------------------------------
# VPC endpoints
#------------------------------------------------------------------------------

resource "aws_vpc_endpoint" "secretsmanager" {
  vpc_id              = aws_vpc.rds-cluster-vpc-prod.id
  service_name        = "com.amazonaws.eu-west-2.secretsmanager"
  subnet_ids          = aws_db_subnet_group.rds-cluster-subnet-group-prod.subnet_ids
  vpc_endpoint_type   = "Interface"
  private_dns_enabled = true

  tags = {
    Name        = "${local.project}-prod-secrets-vpc-endpoint"
    Environment = local.environment
  }
}

resource "aws_vpc_endpoint_security_group_association" "vpc_cluster_security_group_assoc" {
  vpc_endpoint_id   = aws_vpc_endpoint.secretsmanager.id
  security_group_id = aws_security_group.rds-cluster-sg-prod.id
}

resource "aws_vpc_endpoint" "s3" {
  vpc_id       = aws_vpc.rds-cluster-vpc-prod.id
  service_name = "com.amazonaws.eu-west-2.s3"

  tags = {
    Name        = "${local.project}-prod-s3-vpc-endpoint"
    Environment = local.environment
  }
}

resource "aws_vpc_endpoint_route_table_association" "vpc_cluster_route_table_assoc_s3_prod" {
  vpc_endpoint_id = aws_vpc_endpoint.s3.id
  route_table_id  = aws_route_table.private-route-table-prod.id
}
