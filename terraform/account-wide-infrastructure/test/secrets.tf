resource "aws_secretsmanager_secret" "identities_account_id" {
  name = "${local.prefix}--nhs-identities-account-id"
}

resource "aws_secretsmanager_secret" "int_smoke_test_apigee_app" {
  name        = "${local.prefix}--int--apigee-app--smoke-test"
  description = "APIGEE App used to run Smoke Tests against the INT/UAT environment"
}

resource "aws_secretsmanager_secret" "ref_smoke_test_apigee_app" {
  name        = "${local.prefix}--ref--apigee-app--smoke-test"
  description = "APIGEE App used to run Smoke Tests against the REF/QA/TEST environment"
}
