module "firehose__processor" {
  source               = "./modules/firehose"
  assume_account       = var.assume_account
  prefix               = local.prefix
  region               = local.region
  layers               = [module.lambda-utils.layer_arn, module.nrlf.layer_arn, module.third_party.layer_arn]
  environment          = local.environment
  cloudwatch_kms_arn   = module.kms__cloudwatch.kms_arn
  splunk_index         = local.splunk_index
  destination          = contains(local.persistent_environments, local.environment) ? "splunk" : "extended_s3"
  slack_alerts_enabled = contains(local.persistent_environments, local.environment)
}
