resource "aws_secretsmanager_secret" "identities_account_id" {
  name = "${local.prefix}--nhs-identities-account-id"
}

// TODO-NOW - Get new apigee app for test/qa smoke tests
resource "aws_secretsmanager_secret" "test_smoke_test_apigee_app" {
  name        = "${local.prefix}--test--apigee-app--smoke-test"
  description = "APIGEE App used to run Smoke Tests against the QA/TEST environment"
}

resource "aws_secretsmanager_secret" "int_smoke_test_apigee_app" {
  name        = "${local.prefix}--int--apigee-app--smoke-test"
  description = "APIGEE App used to run Smoke Tests against the INT/UAT environment"
}

resource "aws_secretsmanager_secret" "ref_smoke_test_apigee_app" {
  name        = "${local.prefix}--ref--apigee-app--smoke-test"
  description = "APIGEE App used to run Smoke Tests against the REF environment"
}

// TODO-NOW - Get new splunk config for test and testsandbox
resource "aws_secretsmanager_secret" "test_splunk_configuration" {
  name        = "${local.project}--test--splunk-configuration"
  description = "Splunk configuration for the aws_recordlocator_test index"
}

resource "aws_secretsmanager_secret" "test_sandbox_splunk_configuration" {
  name        = "${local.project}--testsandbox--splunk-configuration"
  description = "Splunk configuration for the aws_recordlocator_testsandbox index"
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
