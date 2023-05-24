module "rds" {
  source                = "./modules/reporting"
  name                  = "reporting"
  prefix                = local.prefix
  environment           = local.environment
  rds_instance_class    = var.rds_instance_class
  rds_allocated_storage = var.rds_allocated_storage
  bastion_enabled       = local.environment == "prod" || length(regexall("ci-", local.environment)) > 0 ? false : true
}
