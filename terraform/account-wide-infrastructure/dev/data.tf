data "aws_secretsmanager_secret_version" "identities_account_id" {
  secret_id = aws_secretsmanager_secret.identities_account_id.name
}

data "aws_secretsmanager_secret" "mgmt_account_id" {
  name = "${local.project}--dev--mgmt-account-id"
}

data "aws_secretsmanager_secret_version" "mgmt_account_id" {
  secret_id = data.aws_secretsmanager_secret.mgmt_account_id.name
}

data "aws_caller_identity" "current" {}
