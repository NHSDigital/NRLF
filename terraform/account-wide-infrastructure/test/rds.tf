resource "aws_rds_cluster" "rds-cluster-ref" {
  cluster_identifier          = "nhsd-nrlf-ref-aurora-cluster"
  engine                      = var.engine
  engine_version              = var.engine_version
  availability_zones          = ["eu-west-2a", "eu-west-2b", "eu-west-2c"]
  database_name               = "nhsd_nrlf_ref"
  master_username             = var.user_name
  manage_master_user_password = true
  final_snapshot_identifier   = "nhsd-nrlf-ref-aurora-cluster-final-snapshot-${formatdate("YYYYMMDDhhmmss", timestamp())}"
  vpc_security_group_ids = [
    aws_security_group.rds-cluster-sg-ref.id
  ]
  db_subnet_group_name = aws_db_subnet_group.rds-cluster-subnet-group-ref.name

  lifecycle {
    ignore_changes = [availability_zones]
  }

  tags = {
    Name        = "nhsd-nrlf-ref-aurora-cluster"
    Environment = "ref"
  }
}

resource "aws_rds_cluster_instance" "rds-instance-ref" {
  identifier           = "nhsd-nrlf-ref-instance-aurora"
  cluster_identifier   = aws_rds_cluster.rds-cluster-ref.id
  instance_class       = var.instance_type
  engine               = aws_rds_cluster.rds-cluster-ref.engine
  engine_version       = aws_rds_cluster.rds-cluster-ref.engine_version
  db_subnet_group_name = aws_db_subnet_group.rds-cluster-subnet-group-ref.name

  tags = {
    Name        = "nhsd-nrlf-ref-instance-aurora"
    Environment = "ref"
  }
}

resource "aws_rds_cluster" "rds-cluster-int" {
  cluster_identifier          = "nhsd-nrlf-int-aurora-cluster"
  engine                      = var.engine
  engine_version              = var.engine_version
  availability_zones          = ["eu-west-2a", "eu-west-2b", "eu-west-2c"]
  database_name               = "nhsd_nrlf_int"
  master_username             = var.user_name
  manage_master_user_password = true
  final_snapshot_identifier   = "nhsd-nrlf-int-aurora-cluster-final-snapshot-${formatdate("YYYYMMDDhhmmss", timestamp())}"
  vpc_security_group_ids = [
    aws_security_group.rds-cluster-sg-int.id
  ]
  db_subnet_group_name = aws_db_subnet_group.rds-cluster-subnet-group-int.name

  lifecycle {
    ignore_changes = [availability_zones]
  }

  tags = {
    Name        = "nhsd-nrlf-int-aurora-cluster"
    Environment = "int"
  }
}

resource "aws_rds_cluster_instance" "rds-instance-int" {
  identifier           = "nhsd-nrlf-int-instance-aurora"
  cluster_identifier   = aws_rds_cluster.rds-cluster-int.id
  instance_class       = var.instance_type
  engine               = aws_rds_cluster.rds-cluster-int.engine
  engine_version       = aws_rds_cluster.rds-cluster-int.engine_version
  db_subnet_group_name = aws_db_subnet_group.rds-cluster-subnet-group-int.name

  tags = {
    Name        = "nhsd-nrlf-int-instance-aurora"
    Environment = "int"
  }
}
