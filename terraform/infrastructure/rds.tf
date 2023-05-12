module "rds" {
  source               = "./modules/rds"
  name                 = "reporting"
  prefix               = local.prefix
  db_instance_class    = var.db_instance_class
  db_allocated_storage = var.db_allocated_storage
}
