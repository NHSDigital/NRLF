locals {
  region              = "eu-west-2"
  project             = "nhsd-nrlf"
  account_name        = var.account_name
  environment         = terraform.workspace
  deletion_protection = var.deletion_protection
  prefix              = "${local.project}--${local.environment}"
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
  # Logic / vars for splunk environment
  persistent_environments = ["dev", "dev-sandbox", "qa", "qa-sandbox", "ref", "int", "int-sandbox", "prod"]
  environment_no_hyphen   = replace(local.environment, "-", "")
  splunk_environment      = contains(local.persistent_environments, local.environment) ? local.environment_no_hyphen : "dev" # dev is the default splunk env
  splunk_index            = "aws_recordlocator_${local.splunk_environment}"
  public_domain_map = {
    "dev"         = var.public_domain,
    "dev-sandbox" = var.public_sandbox_domain,
    "qa"          = var.public_domain,
    "qa-sandbox"  = var.public_sandbox_domain,
    "int"         = var.public_domain,
    "int-sandbox" = var.public_sandbox_domain,
    "ref"         = var.public_domain
    "prod"        = var.public_domain,
  }
  public_domain = try(local.public_domain_map[terraform.workspace], local.apis.domain)

  development_environments = ["dev", "dev-sandbox"]
  log_level                = contains(local.persistent_environments, local.environment) ? (contains(local.development_environments, local.environment) ? "DEBUG" : "INFO") : "DEBUG"
  aws_account_id           = data.aws_caller_identity.current.account_id
}
