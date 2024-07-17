resource "aws_cloudwatch_metric_alarm" "metric_alarm" {
  alarm_name        = "${var.name_prefix}--lambda-errors-metric-alarm"
  alarm_description = var.alarm_description

  alarm_actions = [aws_sns_topic.sns_topic.arn]

  comparison_operator = var.comparison_operator
  evaluation_periods  = var.evaluation_periods
  threshold           = var.threshold
  unit                = var.unit

  metric_name = var.metric_name
  namespace   = var.namespace
  period      = var.period
  statistic   = var.statistic

}
