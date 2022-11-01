module "lambda-utils" {
  source = "./modules/layer"
  name   = "lambda_utils"
  prefix = local.prefix
}

module "nrlf" {
  source = "./modules/layer"
  name   = "nrlf"
  prefix = local.prefix
}

module "third_party" {
  source = "./modules/layer"
  name   = "third_party"
  prefix = local.prefix
}
