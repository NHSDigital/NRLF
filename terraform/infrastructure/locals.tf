locals {
  region                       = var.region_name
  project                      = var.project_name
  environment                  = terraform.workspace
  prefix                       = "${local.project}--${local.environment}"
}
