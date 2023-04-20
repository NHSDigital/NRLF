module "firehose__processor" {
  source             = "./modules/firehose"
  prefix             = local.prefix
  region             = local.region
  layers             = [module.lambda-utils.layer_arn, module.nrlf.layer_arn, module.third_party.layer_arn]
  environment        = local.environment
  cloudwatch_kms_arn = module.kms__cloudwatch.kms_arn
  splunk_index       = "aws_recordlocator_${contains(local.persistent_environments, local.environment) ? replace(local.environment, "-", "") : "dev"}"

  # >> UNCOMMENT THE FOLLOWING TO ENABLE SPLUNK AFTER:
  # >> 1) This branch has been deployed to each Persistent Env (dev, dev-sandbox, ... , prod)
  # >> 2) The Splunk HEC/endpoint secret has been updated in each Persistent Env, as described in secrets.tf
  # >> Then once the below has been uncommented then deploy to each Persistent Env
  # destination = contains(local.persistent_environments, local.environment) ? "splunk" : "extended_s3"
}
