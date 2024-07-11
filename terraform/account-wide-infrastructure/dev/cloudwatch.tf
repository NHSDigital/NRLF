module "lambda_errors_cloudwatch_metric_alarm_dev" {
  source      = "./modules/lambda-errors-metric-alarm"
  name_prefix = "nhsd-nrlf--dev"

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
