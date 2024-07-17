module "lambda_errors_cloudwatch_metric_alarm_dev" {
  source      = "../modules/lambda-errors-metric-alarm"
  name_prefix = "nhsd-nrlf--prod"

  evaluation_periods = 1
  period             = 60
  threshold          = 1
}
