module "ephemeral-s3-permission-store" {
  source                     = "../permissions-store-bucket"
  name_prefix                = var.prefix
}