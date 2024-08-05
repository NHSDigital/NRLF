resource "aws_cloudwatch_log_group" "lambda_cloudwatch_log_group" {
  name              = "/aws/lambda/${aws_lambda_function.lambda_function.function_name}"
  retention_in_days = var.retention
  kms_key_id        = var.kms_key_id
}

resource "aws_cloudwatch_log_subscription_filter" "lambda_log_filter" {
  name           = "${aws_lambda_function.lambda_function.function_name}_filter"
  log_group_name = aws_cloudwatch_log_group.lambda_cloudwatch_log_group.name

  count           = length(var.firehose_subscriptions)
  role_arn        = var.firehose_subscriptions[count.index].role.arn
  destination_arn = var.firehose_subscriptions[count.index].destination.arn
  filter_pattern  = var.firehose_subscriptions[count.index].filter.pattern
}
