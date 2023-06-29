resource "aws_rds_cluster" "rds-cluster-prod" {
  cluster_identifier          = "${local.project}-prod-aurora-cluster"
  engine                      = var.engine
  engine_version              = var.engine_version
  availability_zones          = ["eu-west-2a", "eu-west-2b", "eu-west-2c"]
  database_name               = "nhsd_nrlf_prod"
  master_username             = var.user_name
  manage_master_user_password = true
  final_snapshot_identifier   = "${local.project}-prod-aurora-cluster-final-snapshot-${formatdate("YYYYMMDDhhmmss", timestamp())}"
  vpc_security_group_ids = [
    aws_security_group.rds-cluster-sg-prod.id
  ]
  db_subnet_group_name = aws_db_subnet_group.rds-cluster-subnet-group-prod.name

  lifecycle {
    ignore_changes = [availability_zones]
  }

  tags = {
    Name        = "${local.project}-prod-aurora-cluster"
    Environment = local.environment
  }
}

resource "aws_rds_cluster_instance" "rds-instance-prod" {
  identifier           = "${local.project}-prod-instance-aurora"
  cluster_identifier   = aws_rds_cluster.rds-cluster-prod.id
  instance_class       = var.instance_type
  engine               = aws_rds_cluster.rds-cluster-prod.engine
  engine_version       = aws_rds_cluster.rds-cluster-prod.engine_version
  db_subnet_group_name = aws_db_subnet_group.rds-cluster-subnet-group-prod.name

  tags = {
    Name        = "${local.project}-prod-instance-aurora"
    Environment = local.environment
  }
}
