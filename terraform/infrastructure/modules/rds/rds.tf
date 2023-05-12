module "vpc" {
  source               = "terraform-aws-modules/vpc/aws"
  version              = "4.0.1"
  name                 = "${replace(var.prefix, "--", "-")}-${var.name}-rds"
  cidr                 = "10.0.0.0/16"
  azs                  = ["eu-west-2a", "eu-west-2b", "eu-west-2c"]
  public_subnets       = ["10.0.4.0/24", "10.0.5.0/24", "10.0.6.0/24"]
  enable_dns_hostnames = true
  enable_dns_support   = true
}

resource "aws_db_subnet_group" "rds" {
  name       = "${replace(var.prefix, "--", "-")}-${var.name}-rds"
  subnet_ids = module.vpc.public_subnets
}

resource "aws_db_instance" "rds" {
  identifier             = "${replace(var.prefix, "--", "-")}-${var.name}-rds"
  instance_class         = var.db_instance_class
  allocated_storage      = var.db_allocated_storage
  engine                 = "postgres"
  engine_version         = "14.1"
  username               = "nrlfadmin"
  password               = random_password.rds_password.result
  db_subnet_group_name   = aws_db_subnet_group.rds.name
  vpc_security_group_ids = [aws_security_group.rds.id]
  parameter_group_name   = aws_db_parameter_group.rds.name
  publicly_accessible    = true
  skip_final_snapshot    = true
}

resource "aws_security_group" "rds" {
  name   = "${replace(var.prefix, "--", "-")}-${var.name}-rds"
  vpc_id = module.vpc.vpc_id

  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_db_parameter_group" "rds" {
  name   = "rds"
  family = "postgres14"

  parameter {
    name  = "log_connections"
    value = "1"
  }
}
