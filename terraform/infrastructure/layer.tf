module "nrlf" {
  source = "./modules/layer"
  name   = "nrlf"
  prefix = local.prefix
}

module "third_party" {
  source = "./modules/layer"
  name   = "dependency_layer"
  prefix = local.prefix
}

module "s3" {
  source = "./modules/layer"
  name   = "nrlf_permissions"
  prefix = local.prefix
}
