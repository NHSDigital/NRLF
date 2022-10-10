module "kms__cloudwatch" {
  source         = "./modules/kms"
  name           = "cloudwatch"
  assume_account = var.assume_account
  prefix         = local.prefix
}

module "kms__custodian" {
  source         = "./modules/kms_read_write_policy"
  name           = "custodian"
  assume_account = var.assume_account
  prefix         = local.prefix
}

module "kms__document-reference" {
  source         = "./modules/kms_read_write_policy"
  name           = "document-reference"
  assume_account = var.assume_account
  prefix         = local.prefix
}
