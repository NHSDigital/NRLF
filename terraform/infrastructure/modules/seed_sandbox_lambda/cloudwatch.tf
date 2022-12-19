resource "aws_cloudwatch_log_group" "lambda_cloudwatch_log_group" {
  name              = "/aws/lambda/${aws_lambda_function.lambda_function.function_name}"
  retention_in_days = local.lambda_log_retention_in_days
  kms_key_id        = var.kms_key_id
}


resource "aws_cloudwatch_event_rule" "event_rule" {
  name                = "${var.prefix}--event_rule"
  description         = "Rule to fire to clear and reseed sandbox data"
  schedule_expression = "cron(0 3 ? * * *)" # 3am, every day
}

resource "aws_cloudwatch_event_target" "event_target" {
  target_id = "${var.prefix}--event_target"
  rule      = aws_cloudwatch_event_rule.event_rule.name
  arn       = aws_lambda_function.lambda_function.arn
}


resource "aws_lambda_permission" "allow_execution_from_cloudwatch" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.lambda_function.arn
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.event_rule.arn
}
