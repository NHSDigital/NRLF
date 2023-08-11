#------------------------------------------------------------------------------
# Security Group
#------------------------------------------------------------------------------

# Any resources deployed to this security group will need deleting before modifying this
resource "aws_security_group" "rds-cluster-sg-prod" {
  name        = "nhsd-nrlf-rds-cluster-sg-prod"
  description = "Security group for nhsd-nrlf-rds-cluster-vpc"
  vpc_id      = aws_vpc.rds-cluster-vpc-prod.id

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

  #SecretsManager vpc endpoint port
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "TCP"
    cidr_blocks = ["0.0.0.0/0"]
  }

  #SecretsManager vpc endpoint port
  egress {
    from_port   = 443
    to_port     = 443
    protocol    = "TCP"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "nhsd-nrlf-rds-cluster-sg-prod"
    Environment = "prod"
  }
}
