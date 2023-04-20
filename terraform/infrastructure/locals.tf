locals {
  region       = "eu-west-2"
  project      = "nhsd-nrlf"
  account_name = var.account_name
  environment  = terraform.workspace
  prefix       = "${local.project}--${local.environment}"
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
  persistent_environments = ["dev", "dev-sandbox", "ref", "ref-sandbox", "int", "prod"]
}
