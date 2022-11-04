locals {
  region      = "eu-west-2"
  project     = "nhsd-nrlf"
  environment = terraform.workspace
  prefix      = "${local.project}--${local.environment}"
}
