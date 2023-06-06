data "aws_vpc" "rds-cluster-vpc" {
  tags = {
    Name        = "nhsd-nrlf-rds-cluster-vpc-${var.account_name}"
    Environment = var.account_name
  }
}

data "aws_subnets" "rds-cluster-vpc-private-subnets" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.rds-cluster-vpc.id]
  }

  tags = {
    Tier = "private"
  }
}

data "aws_db_subnet_group" "rds-cluster-subnet-group" {
  name = "nhsd-nrlf-private-subnet-group-${var.account_name}"
}
