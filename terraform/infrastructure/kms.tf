module "kms__cloudwatch" {
  source         = "./modules/kms"
  name           = "cloudwatch"
  assume_account = var.assume_account
  prefix         = local.prefix
}
