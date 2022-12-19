
module "seed_sandbox_lambda" {
  count      = endswith(local.environment, "-sandbox") ? 1 : 0
  source     = "./modules/seed_sandbox_lambda"
  region     = local.region
  prefix     = local.prefix
  layers     = [module.lambda-utils.layer_arn, module.nrlf.layer_arn, module.third_party.layer_arn]
  kms_key_id = module.kms__cloudwatch.kms_arn
  environment_variables = {
    PREFIX      = "${local.prefix}--"
    ENVIRONMENT = local.environment
  }
  additional_policies = [
    aws_iam_policy.document-pointer__dynamodb-write.arn,
    aws_iam_policy.document-pointer__dynamodb-read.arn,
    aws_iam_policy.document-pointer__kms-read-write.arn,
    aws_iam_policy.auth_consumer__dynamodb-read.arn,
    aws_iam_policy.auth_consumer__dynamodb-write.arn,
    aws_iam_policy.auth_consumer__kms-read-write.arn,
    aws_iam_policy.auth_producer__dynamodb-read.arn,
    aws_iam_policy.auth_producer__dynamodb-write.arn,
    aws_iam_policy.auth_producer__kms-read-write.arn
  ]
}
