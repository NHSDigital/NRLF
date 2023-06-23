resource "aws_rds_cluster" "rds-cluster-ref" {
  cluster_identifier          = "${local.project}-ref-aurora-cluster"
  engine                      = var.engine
  engine_version              = var.engine_version
  availability_zones          = ["eu-west-2a", "eu-west-2b", "eu-west-2c"]
  database_name               = "nhsd_nrlf_ref"
  master_username             = var.user_name
  manage_master_user_password = true
  final_snapshot_identifier   = "${local.project}-ref-aurora-cluster-final-snapshot-${formatdate("YYYYMMDDhhmmss", timestamp())}"
  vpc_security_group_ids = [
    aws_security_group.rds-cluster-sg-ref.id
  ]
  db_subnet_group_name = aws_db_subnet_group.rds-cluster-subnet-group-ref.name

  lifecycle {
    ignore_changes = [availability_zones]
  }

  tags = {
    Name        = "${local.project}-ref-aurora-cluster"
    Environment = "ref"
  }
}

resource "aws_rds_cluster_instance" "rds-instance-ref" {
  identifier           = "${local.project}-ref-instance-aurora"
  cluster_identifier   = aws_rds_cluster.rds-cluster-ref.id
  instance_class       = var.instance_type
  engine               = aws_rds_cluster.rds-cluster-ref.engine
  engine_version       = aws_rds_cluster.rds-cluster-ref.engine_version
  db_subnet_group_name = aws_db_subnet_group.rds-cluster-subnet-group-ref.name

  tags = {
    Name        = "${local.project}-ref-instance-aurora"
    Environment = "ref"
  }
}

resource "aws_rds_cluster" "rds-cluster-int" {
  cluster_identifier          = "${local.project}-int-aurora-cluster"
  engine                      = var.engine
  engine_version              = var.engine_version
  availability_zones          = ["eu-west-2a", "eu-west-2b", "eu-west-2c"]
  database_name               = "nhsd_nrlf_int"
  master_username             = var.user_name
  manage_master_user_password = true
  final_snapshot_identifier   = "${local.project}-int-aurora-cluster-final-snapshot-${formatdate("YYYYMMDDhhmmss", timestamp())}"
  vpc_security_group_ids = [
    aws_security_group.rds-cluster-sg-int.id
  ]
  db_subnet_group_name = aws_db_subnet_group.rds-cluster-subnet-group-int.name

  lifecycle {
    ignore_changes = [availability_zones]
  }

  tags = {
    Name        = "${local.project}-int-aurora-cluster"
    Environment = "int"
  }
}

resource "aws_rds_cluster_instance" "rds-instance-int" {
  identifier           = "${local.project}-int-instance-aurora"
  cluster_identifier   = aws_rds_cluster.rds-cluster-int.id
  instance_class       = var.instance_type
  engine               = aws_rds_cluster.rds-cluster-int.engine
  engine_version       = aws_rds_cluster.rds-cluster-int.engine_version
  db_subnet_group_name = aws_db_subnet_group.rds-cluster-subnet-group-int.name

  tags = {
    Name        = "${local.project}-int-instance-aurora"
    Environment = "int"
  }
}
