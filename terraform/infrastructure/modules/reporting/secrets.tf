resource "random_password" "rds_password" {
  length  = 17
  special = false
}

resource "aws_secretsmanager_secret" "rds_password" {
  name                    = "${replace(var.prefix, "--", "-")}-${var.name}-rds"
  description             = "Password for ${replace(var.prefix, "--", "-")}-${var.name}-rds"
  recovery_window_in_days = var.prefix == "prod" ? 30 : 0
}

resource "aws_secretsmanager_secret_version" "rds_password" {
  secret_id = aws_secretsmanager_secret.rds_password.id
  secret_string = jsonencode({
    username = aws_db_instance.rds.username
    password = aws_db_instance.rds.password
  })
}
