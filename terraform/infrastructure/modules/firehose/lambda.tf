module "lambda" {
  source     = "../lambda"
  apitype    = var.apitype
  name       = "firehose"
  region     = var.region
  prefix     = var.prefix
  layers     = var.layers
  kms_key_id = var.cloudwatch_kms_arn
  environment_variables = {
    PREFIX      = "${var.prefix}--"
    ENVIRONMENT = var.environment
  }
  additional_policies = [
    aws_iam_policy.lambda.arn,
  ]
  handler = "api.${var.apitype}.firehose.index.handler"
}
