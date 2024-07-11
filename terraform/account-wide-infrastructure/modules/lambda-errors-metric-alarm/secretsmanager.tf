data "aws_secretsmanager_secret" "emails" {
  name = "${var.name_prefix}-emails"
}

data "aws_secretsmanager_secret_version" "emails" {
  secret_id = data.aws_secretsmanager_secret.emails.id

}
