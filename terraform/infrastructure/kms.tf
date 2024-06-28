module "kms__cloudwatch" {
  source         = "./modules/kms"
  name           = "cloudwatch"
  assume_account = local.aws_account_id
  prefix         = local.prefix
}
