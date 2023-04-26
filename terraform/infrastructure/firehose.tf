module "firehose__processor" {
  source             = "./modules/firehose"
  assume_account     = var.assume_account
  prefix             = local.prefix
  region             = local.region
  layers             = [module.lambda-utils.layer_arn, module.nrlf.layer_arn, module.third_party.layer_arn]
  environment        = local.environment
  cloudwatch_kms_arn = module.kms__cloudwatch.kms_arn
  splunk_index       = local.splunk_index
  destination        = contains(local.persistent_environments, local.environment) ? "splunk" : "extended_s3"

  # >> UNCOMMENT THE FOLLOWING TO ENABLE SLACK ALERTS AFTER:
  # >> 1) This branch has been deployed to each Persistent Env (dev, dev-sandbox, ... , prod)
  # >> 2) The Slack webhook secret has been updated in each Persistent Env, as described in secrets.tf
  # >> Then once the below has been uncommented then deploy to each Persistent Env
  # slack_alerts_enabled = contains(local.persistent_environments, local.environment)
}
