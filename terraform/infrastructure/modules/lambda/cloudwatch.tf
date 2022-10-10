resource "aws_cloudwatch_log_group" "lambda_cloudwatch_log_group" {
  name              = "/aws/lambda/${substr("${var.prefix}--api--${var.apitype}--${var.name}", 0, 64)}"
  retention_in_days = local.lambda_log_retention_in_days

  kms_key_id = var.kms_key_id

}
