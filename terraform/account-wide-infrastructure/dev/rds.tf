resource "aws_rds_cluster" "rds-cluster-dev" {
  cluster_identifier          = "${local.project}-dev-aurora-cluster"
  engine                      = var.engine
  engine_version              = var.engine_version
  availability_zones          = ["eu-west-2a", "eu-west-2b", "eu-west-2c"]
  database_name               = "nhsd_nrlf_dev"
  master_username             = var.user_name
  manage_master_user_password = true
  final_snapshot_identifier   = "${local.project}-dev-aurora-cluster-final-snapshot-${formatdate("YYYYMMDDhhmmss", timestamp())}"
  vpc_security_group_ids = [
    aws_security_group.rds-cluster-sg-dev.id
  ]
  db_subnet_group_name = aws_db_subnet_group.rds-cluster-subnet-group-dev.name

  lifecycle {
    ignore_changes = [availability_zones]
  }

  tags = {
    Name        = "${local.project}-dev-aurora-cluster"
    Environment = local.environment
  }
}

resource "aws_rds_cluster_instance" "rds-instance-dev" {
  identifier           = "${local.project}-dev-instance-aurora"
  cluster_identifier   = aws_rds_cluster.rds-cluster-dev.id
  instance_class       = var.instance_type
  engine               = aws_rds_cluster.rds-cluster-dev.engine
  engine_version       = aws_rds_cluster.rds-cluster-dev.engine_version
  db_subnet_group_name = aws_db_subnet_group.rds-cluster-subnet-group-dev.name

  tags = {
    Name        = "${local.project}-dev-instance-aurora"
    Environment = local.environment
  }
}
