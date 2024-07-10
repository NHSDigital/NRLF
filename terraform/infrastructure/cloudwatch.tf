module "lambda_errors_sns_topic" {
  source = "./modules/sns"
  name   = "nrlf_lambda_errors_topic"
  prefix = local.prefix
}

module "lambda_errors_cloudwatch_metric_alarm" {
  source = "./modules/cloudwatch"
  name   = "nrlf_lambda_errors"
  prefix = local.prefix

  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 1
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = 60
  statistic           = "Maximum"
  threshold           = 0
  unit                = "Count"
  alarm_description   = "This metric monitors the number of Lambda errors that have occurred"
  alarm_actions       = [module.lambda_errors_sns_topic.sns_topic_arn]
}

module "lambda_errors_topic_subscription_slack" {
  source    = "./modules/sns"
  prefix    = local.prefix
  name      = "slack_email_subscription"
  topic_arn = module.aws_sns_topic.sns_topic_arn
  protocol  = "email"
  endpoint  = "spine-cell-sigma-noti-aaaalor2u6funj7q3a4v7cpuba@nhsdigitalcorporate.org.slack.com"
}

module "lambda_errors_topic_subscription_me" {
  source    = "./modules/sns"
  prefix    = local.prefix
  name      = "me_email_subscription"
  topic_arn = module.aws_sns_topic.sns_topic_arn
  protocol  = "email"
  endpoint  = "eesa.mahmood1@nhs.net"
}
