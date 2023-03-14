module "producer__firehose" {
  source             = "./modules/firehose"
  prefix             = local.prefix
  region             = local.region
  apitype            = "producer"
  layers             = [module.lambda-utils.layer_arn, module.nrlf.layer_arn, module.third_party.layer_arn]
  environment        = local.environment
  cloudwatch_kms_arn = module.kms__cloudwatch.kms_arn
}

# module "consumer__firehose" {
#   source             = "./modules/firehose"
#   prefix             = local.prefix
#   region             = local.region
#   apitype            = "consumer"
#   layers             = [module.lambda-utils.layer_arn, module.nrlf.layer_arn, module.third_party.layer_arn]
#   environment        = local.environment
#   cloudwatch_kms_arn = module.kms__cloudwatch.kms_arn
# }
