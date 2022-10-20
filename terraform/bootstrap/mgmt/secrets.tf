resource "aws_secretsmanager_secret" "mgmt_account_id" {
  name = "${local.prefix}--mgmt-account-id"
}

resource "aws_secretsmanager_secret" "dev_account_id" {
  name = "${local.prefix}--dev-account-id"
}

resource "aws_secretsmanager_secret" "test_account_id" {
  name = "${local.prefix}--test-account-id"
}

resource "aws_secretsmanager_secret" "prod_account_id" {
  name = "${local.prefix}--prod-account-id"
}
