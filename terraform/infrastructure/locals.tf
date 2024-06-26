locals {
  region              = "eu-west-2"
  project             = "nhsd-nrlf"
  environment         = terraform.workspace
  deletion_protection = var.deletion_protection
  prefix              = "${local.project}--${local.environment}"
  shared_prefix       = "${local.project}--${var.account_name}"
  kms = {
    deletion_window_in_days = 7
  }

  # TODO - Remove once all environments are on new domain structure
  env_on_new_dns_zone = ["qa", "qa-sandbox"]
  new_domain_map = {
    "qa" : "api.${var.domain}",
    "qa-sandbox" : "sandbox-api.${var.domain}",
  }

  apis = {
    zone = var.domain
    # TODO - Move all other environments onto new domain structure
    domain = contains(local.env_on_new_dns_zone, local.environment) ? local.new_domain_map[local.environment] : "${terraform.workspace}.${var.domain}"
    consumer = {
      path = var.consumer_api_path
    }
    producer = {
      path = var.producer_api_path
    }
  }
  dynamodb_timeout_seconds = "3"

  persistent_environments = ["dev", "dev-sandbox", "qa", "qa-sandbox", "ref", "int", "int-sandbox", "prod"]
  is_persistent_env       = contains(local.persistent_environments, local.environment)
  is_sandbox_env          = length(regexall("-sandbox", local.environment)) > 0
  is_dev_env              = local.environment == "dev" || local.environment == "dev-sandbox"

  public_domain = local.is_persistent_env ? local.is_sandbox_env ? var.public_sandbox_domain : var.public_domain : local.apis.domain

  # Logic / vars for splunk environment
  environment_no_hyphen = replace(local.environment, "-", "")
  splunk_environment    = local.is_persistent_env ? local.environment_no_hyphen : "dev" # dev is the default splunk env
  splunk_index          = "aws_recordlocator_${local.splunk_environment}"

  log_level = local.is_persistent_env ? local.is_dev_env ? "DEBUG" : "INFO" : "DEBUG"

  aws_account_id = data.aws_caller_identity.current.account_id
}
