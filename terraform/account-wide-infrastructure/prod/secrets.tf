resource "aws_secretsmanager_secret" "identities_account_id" {
  name = "${local.prefix}--nhs-identities-account-id"
}

resource "aws_secretsmanager_secret" "prod_smoke_test_apigee_app" {
  name        = "${local.prefix}--prod--apigee-app--smoke-test"
  description = "APIGEE App used to run Smoke Tests against the PROD environment"
}

resource "aws_secretsmanager_secret" "prod_splunk_configuration" {
  name        = "${local.project}--prod--splunk-configuration"
  description = "Splunk configuration for the aws_recordlocator_prod index"
}

resource "aws_secretsmanager_secret" "prod_environment_configuration" {
  name        = "${local.project}--prod--env-config"
  description = "The environment configuration for the Prod environment"
}
