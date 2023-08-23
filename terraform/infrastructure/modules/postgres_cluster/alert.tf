module "mi_alert_lambda" {
  source      = "../lambda"
  parent_path = var.name
  name        = "mi_alert"
  region      = var.region
  prefix      = var.prefix
  layers      = concat(var.layers, [module.nrlf.layer_arn])
  kms_key_id  = var.cloudwatch_kms_arn
  environment_variables = {
    PREFIX            = "${var.prefix}--"
    ENVIRONMENT       = var.environment
    SLACK_WEBHOOK_URL = jsonencode(data.aws_secretsmanager_secret_version.slack_webhook_url.*.secret_string)
  }
  additional_policies = [aws_iam_policy.mi-errors-alert--s3-read.arn]
  handler             = "mi.mi_alert.index.handler"
}

resource "aws_lambda_permission" "s3_bucket_can_invoke_lambda" {
  statement_id  = "AllowExecutionFromS3Bucket"
  action        = "lambda:InvokeFunction"
  function_name = module.mi_alert_lambda.arn
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.mi-errors.arn
}

resource "aws_s3_bucket_notification" "alert" {
  bucket = aws_s3_bucket.mi-errors.id

  lambda_function {
    lambda_function_arn = module.mi_alert_lambda.arn
    events              = ["s3:ObjectCreated:*"]
  }

  depends_on = [aws_lambda_permission.s3_bucket_can_invoke_lambda]
}

resource "aws_secretsmanager_secret" "slack_webhook_url" {
  name        = "${var.prefix}--mi-alert--slack-webhook-url"
  description = "Slack webhook URL for Mi alerts"
}

data "aws_secretsmanager_secret_version" "slack_webhook_url" {
  count     = var.is_persistent_environment ? 1 : 0
  secret_id = aws_secretsmanager_secret.slack_webhook_url.name
}
