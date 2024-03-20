module "firehose__processor" {
  source             = "./modules/firehose"
  assume_account     = var.assume_account
  prefix             = local.prefix
  region             = local.region
  environment        = local.environment
  cloudwatch_kms_arn = module.kms__cloudwatch.kms_arn
  splunk_index       = local.splunk_index
  destination        = "splunk"
}
