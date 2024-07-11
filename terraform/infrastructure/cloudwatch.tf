module "lambda_errors_sns_topic" {
  source = "./modules/sns"
  name   = "nrlf_lambda_errors_topic"
  prefix = local.prefix
}

module "lambda_errors_cloudwatch_metric_alarm" {
  source = "./modules/cloudwatch"
  name   = "nrlf-lambda-errors"
  prefix = local.prefix

  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 1
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = 60
  statistic           = "Maximum"
  threshold           = 1
  unit                = "Count"
  alarm_description   = "This metric monitors the number of Lambda errors that have occurred"
  alarm_actions       = [module.lambda_errors_sns_topic.sns_topic_arn]
}
