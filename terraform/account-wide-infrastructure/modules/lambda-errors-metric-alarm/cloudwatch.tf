resource "aws_cloudwatch_metric_alarm" "metric_alarm" {
  alarm_name        = "${var.name_prefix}--lambda-errors-metric-alarm"
  alarm_description = "This metric monitors the number of Lambda errors that have occurred"

  alarm_actions = [aws_sns_topic.sns_topic.arn]

  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = var.evaluation_periods
  threshold           = var.threshold
  unit                = "Count"

  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = var.period
  statistic           = "Sum"
  datapoints_to_alarm = 1

}
