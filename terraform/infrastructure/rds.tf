module "rds" {
  source                = "./modules/rds"
  name                  = "reporting"
  prefix                = local.prefix
  environment           = local.environment
  rds_instance_class    = var.rds_instance_class
  rds_allocated_storage = var.rds_allocated_storage
}
