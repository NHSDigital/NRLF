module "alert_lambda" {
  source      = "../lambda"
  parent_path = "firehose"
  name        = "alert"
  region      = var.region
  prefix      = var.prefix
  layers      = var.layers
  kms_key_id  = var.cloudwatch_kms_arn
  environment_variables = {
    PREFIX            = "${var.prefix}--"
    ENVIRONMENT       = var.environment
    SPLUNK_INDEX      = var.splunk_index
    SLACK_WEBHOOK_URL = jsonencode(data.aws_secretsmanager_secret_version.slack_webhook_url.*.secret_string)
  }
  additional_policies = [aws_iam_policy.firehose-alert--s3-read.arn]
  handler             = "firehose.alert.index.handler"
}

resource "aws_lambda_permission" "s3_bucket_can_invoke_lambda" {
  statement_id  = "AllowExecutionFromS3Bucket"
  action        = "lambda:InvokeFunction"
  function_name = module.alert_lambda.arn
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.firehose.arn
}

resource "aws_s3_bucket_notification" "alert" {
  bucket = aws_s3_bucket.firehose.id

  lambda_function {
    lambda_function_arn = module.alert_lambda.arn
    events              = ["s3:ObjectCreated:*"]
    filter_prefix       = "errors/"
  }

  depends_on = [aws_lambda_permission.s3_bucket_can_invoke_lambda]
}
