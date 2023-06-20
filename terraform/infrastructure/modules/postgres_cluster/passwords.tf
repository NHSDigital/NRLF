resource "random_password" "write_password" {
  length = 16
}

resource "aws_secretsmanager_secret" "write_password" {
  name = "${var.prefix}--${var.environment}--write_password"
}

resource "aws_secretsmanager_secret_version" "write_password" {
  secret_id     = aws_secretsmanager_secret.write_password.id
  secret_string = random_password.write_password.result
}


resource "random_password" "read_password" {
  length = 16
}

resource "aws_secretsmanager_secret" "read_password" {
  name = "${var.prefix}--${var.environment}--read_password"
}

resource "aws_secretsmanager_secret_version" "read_password" {
  secret_id     = aws_secretsmanager_secret.read_password.id
  secret_string = random_password.read_password.result
}

data "aws_secretsmanager_secret_version" "master_user_password" {
  secret_id = data.aws_rds_cluster.rds-cluster.master_user_secret.0.secret_arn
}
