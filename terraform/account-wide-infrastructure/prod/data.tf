data "aws_secretsmanager_secret_version" "identities_account_id" {
  secret_id = aws_secretsmanager_secret.identities_account_id.name
}

data "aws_caller_identity" "current" {}
