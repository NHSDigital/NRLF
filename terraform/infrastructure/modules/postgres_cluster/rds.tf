# data "aws_rds_cluster" "rds-cluster" {
#   cluster_identifier = "arn:aws:rds:${var.region}:${var.assume_account}:cluster:nhsd-nrlf-${var.account_name}-aurora-cluster"
#   tags = {
#     Name        = "${var.prefix}-${var.account_name}-aurora-cluster"
#     Environment = var.account_name
#   }
# }

# data "aws_db_instance" "rds-instance" {
#   db_instance_identifier = "nhsd-nrlf-${var.account_name}-instance-aurora"
# }
