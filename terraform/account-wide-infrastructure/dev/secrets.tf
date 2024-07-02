resource "aws_secretsmanager_secret" "identities_account_id" {
  name = "${local.prefix}--nhs-identities-account-id"
}

resource "aws_secretsmanager_secret" "dev_smoke_test_apigee_app" {
  name        = "${local.prefix}--dev--apigee-app--smoke-test"
  description = "APIGEE App used to run Smoke Tests against the DEV environment"
}

resource "aws_secretsmanager_secret" "dev_splunk_configuration" {
  name        = "${local.project}--dev--splunk-configuration"
  description = "Splunk configuration for the aws_recordlocator_dev index"
}

resource "aws_secretsmanager_secret" "devsandbox_splunk_configuration" {
  name        = "${local.project}--devsandbox--splunk-configuration"
  description = "Splunk configuration for the aws_recordlocator_devsandbox index"
}

resource "aws_secretsmanager_secret" "dev_environment_configuration" {
  name        = "${local.project}--dev--env-config"
  description = "The environment configuration for the Dev environment"
}

resource "aws_secretsmanager_secret" "devsandbox_environment_configuration" {
  name        = "${local.project}--devsandbox--env-config"
  description = "The environment configuration for the Dev Sandbox environment"
}
