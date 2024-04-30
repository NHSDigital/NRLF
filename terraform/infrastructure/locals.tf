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
  apis = {
    # e.g. api.record-locator.dev.national.nhs.uk
    zone = var.domain
    # If terraform workspace = root workspace then don't use sub-domain
    # e.g. 00d5ff61.api.record-locator.dev.national.nhs.uk for PR
    #      api.record-locator.dev.national.nhs.uk for dev
    domain = "${terraform.workspace}.${var.domain}"
    consumer = {
      path = var.consumer_api_path
    }
    producer = {
      path = var.producer_api_path
    }
  }
  dynamodb_timeout_seconds = "3"
  # Logic / vars for splunk environment
  persistent_environments = ["dev", "dev-sandbox", "test", "test-sandbox", "ref", "ref-sandbox", "int", "int-sandbox", "prod"]
  environment_no_hyphen   = replace(local.environment, "-", "")
  splunk_environment      = contains(local.persistent_environments, local.environment) ? local.environment_no_hyphen : "dev" # dev is the default splunk env
  splunk_index            = "aws_recordlocator_${local.splunk_environment}"
  public_domain_map = {
    "int"         = "int.api.service.nhs.uk",
    "dev"         = "internal-dev.api.service.nhs.uk", // TODO-NOW - Is this domain correct? Everywhere else references it as dev.api.service.nhs.uk
    "test"        = "test.api.service.nhs.uk",
    "ref"         = "ref.api.service.nhs.uk",
    "int-sandbox" = "sandbox.api.service.nhs.uk",
    "prod"        = "api.service.nhs.uk",
  }
  public_domain = try(local.public_domain_map[terraform.workspace], local.apis.domain)

  development_environments = ["dev", "dev-sandbox", "v2"] // TODO-NOW - Can we remove v2 from this list now?
  log_level                = contains(local.persistent_environments, local.environment) ? (contains(local.development_environments, local.environment) ? "DEBUG" : "INFO") : "DEBUG"
  aws_account_id           = data.aws_caller_identity.current.account_id
}
