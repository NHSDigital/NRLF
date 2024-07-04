locals {
  region              = "eu-west-2"
  project             = "nhsd-nrlf"
  environment         = var.account_name
  stack_name          = terraform.workspace
  deletion_protection = var.deletion_protection
  prefix              = "${local.project}--${local.stack_name}"
  shared_prefix       = "${local.project}--${local.environment}"

  kms = {
    deletion_window_in_days = 7
  }

  apis = {
    zone   = var.domain
    domain = "${terraform.workspace}.${var.domain}"
    consumer = {
      path = var.consumer_api_path
    }
    producer = {
      path = var.producer_api_path
    }
  }
  dynamodb_timeout_seconds = "3"

  is_sandbox_env = length(regexall("-sandbox", local.environment)) > 0

  public_domain = local.is_sandbox_env ? var.public_sandbox_domain : var.public_domain

  # Logic / vars for splunk environment
  splunk_environment = local.is_sandbox_env ? "${var.account_name}sandbox" : var.account_name
  splunk_index       = "aws_recordlocator_${local.splunk_environment}"

  log_level = var.account_name == "dev" || var.account_name == "qa" ? "DEBUG" : "INFO"

  aws_account_id = data.aws_caller_identity.current.account_id

  auth_store_id  = var.use_shared_resources ? data.aws_s3_bucket.authorization-store[0].id : module.ephemeral-s3-permission-store[0].bucket_id
  auth_store_arn = var.use_shared_resources ? data.aws_s3_bucket.authorization-store[0].arn : module.ephemeral-s3-permission-store[0].bucket_arn

  pointers_table_name             = var.use_shared_resources ? data.aws_dynamodb_table.pointers-table[0].name : module.ephemeral-pointers-table[0].table_name
  pointers_table_read_policy_arn  = var.use_shared_resources ? data.aws_iam_policy.pointers-table-read[0].arn : module.ephemeral-pointers-table[0].read_policy_arn
  pointers_table_write_policy_arn = var.use_shared_resources ? data.aws_iam_policy.pointers-table-write[0].arn : module.ephemeral-pointers-table[0].write_policy_arn
  pointers_kms_read_write_arn     = var.use_shared_resources ? data.aws_iam_policy.pointers-kms-read-write[0].arn : module.ephemeral-pointers-table[0].kms_read_write_policy_arn
}
