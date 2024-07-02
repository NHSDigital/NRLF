module "ephemeral-s3-permission-store" {
  count                       = var.use_shared_resources ? 0 : 1
  source                      = "./modules/permissions-store-bucket"
  name_prefix                 = local.prefix
  enable_bucket_force_destroy = true
}

module "ephemeral-pointers-table" {
  count       = var.use_shared_resources ? 0 : 1
  source      = "./modules/pointers-table"
  name_prefix = local.prefix
}
