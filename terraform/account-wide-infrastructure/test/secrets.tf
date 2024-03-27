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

resource "aws_secretsmanager_secret" "int_splunk_configuration" {
  name        = "${local.project}--int--splunk-configuration"
  description = "Splunk configuration for the aws_recordlocator_int index"
}

resource "aws_secretsmanager_secret" "int_sandbox_splunk_configuration" {
  name        = "${local.project}--intsandbox--splunk-configuration"
  description = "Splunk configuration for the aws_recordlocator_intsandbox index"
}

resource "aws_secretsmanager_secret" "ref_splunk_configuration" {
  name        = "${local.project}--ref--splunk-configuration"
  description = "Splunk configuration for the aws_recordlocator_ref index"
}

resource "aws_secretsmanager_secret" "ref_sandbox_splunk_configuration" {
  name        = "${local.project}--refsandbox--splunk-configuration"
  description = "Splunk configuration for the aws_recordlocator_refsandbox index"
}
