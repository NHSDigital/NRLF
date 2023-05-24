resource "aws_security_group" "bastion" {
  name        = "${replace(var.prefix, "--", "-")}-${var.name}-sg-bastion"
  description = "Security group for ${replace(var.prefix, "--", "-")}-${var.name}-bastion"
  vpc_id      = aws_vpc.vpc.id

  ingress {
    from_port        = 443
    to_port          = 443
    protocol         = "TCP"
    ipv6_cidr_blocks = ["::/0"]
    cidr_blocks      = ["0.0.0.0/0"]
  }

  ingress {
    from_port        = 80
    to_port          = 80
    protocol         = "TCP"
    ipv6_cidr_blocks = ["::/0"]
    cidr_blocks      = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = -1
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "${var.prefix}-Bastion-SG"
    Environment = var.environment
  }
}

resource "aws_security_group" "rds" {
  name        = "${replace(var.prefix, "--", "-")}-${var.name}-sg-rds"
  description = "Security group for ${replace(var.prefix, "--", "-")}-${var.name}-rds"
  vpc_id      = aws_vpc.vpc.id

  ingress {
    description     = "Allow PSQL traffic from the Bastion Security Group"
    from_port       = 5432
    to_port         = 5432
    protocol        = "TCP"
    security_groups = [aws_security_group.bastion.id]
  }

  tags = {
    Name        = "${var.prefix}-RDS-SG"
    Environment = var.environment
  }
}

resource "aws_db_subnet_group" "rds" {
  name       = "${replace(var.prefix, "--", "-")}-${var.name}-rds"
  subnet_ids = [for subnet in aws_subnet.private_subnet : subnet.id]
}
