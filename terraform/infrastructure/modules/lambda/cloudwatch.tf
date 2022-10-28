resource "aws_cloudwatch_log_group" "lambda_cloudwatch_log_group" {
  name              = "/aws/lambda/${aws_lambda_function.lambda_function.function_name}"
  retention_in_days = local.lambda_log_retention_in_days

  kms_key_id = var.kms_key_id

}
