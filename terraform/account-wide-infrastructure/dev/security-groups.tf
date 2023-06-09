#------------------------------------------------------------------------------
# Security Group
#------------------------------------------------------------------------------

# Any resources deployed to this security group will need deleting before modifying this
resource "aws_security_group" "rds-cluster-sg-dev" {
  name        = "nhsd-nrlf-rds-cluster-sg-dev"
  description = "Security group for nhsd-nrlf-rds-cluster-vpc"
  vpc_id      = aws_vpc.rds-cluster-vpc-dev.id

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
    Name        = "nhsd-nrlf-rds-cluster-sg-dev"
    Environment = "dev"
  }
}
