#------------------------------------------------------------------------------
# Security Group
#------------------------------------------------------------------------------

# Any resources deployed to this security group will need deleting before modifying this
resource "aws_security_group" "rds-cluster-sg-ref" {
  name        = "nhsd-nrlf-rds-cluster-sg-ref"
  description = "Security group for nhsd-nrlf-rds-cluster-vpc"
  vpc_id      = aws_vpc.rds-cluster-vpc-ref.id

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
    Name        = "nhsd-nrlf-rds-cluster-sg-ref"
    Environment = "ref"
  }
}

resource "aws_security_group" "rds-cluster-sg-int" {
  name        = "nhsd-nrlf-rds-cluster-sg-int"
  description = "Security group for nhsd-nrlf-rds-cluster-vpc"
  vpc_id      = aws_vpc.rds-cluster-vpc-int.id

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
    Name        = "nhsd-nrlf-rds-cluster-sg-int"
    Environment = "int"
  }
}
