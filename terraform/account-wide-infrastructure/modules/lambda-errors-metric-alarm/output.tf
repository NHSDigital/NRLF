output "cloudwatch_metric_alarm_arn" {
  description = "The ARN of the Cloudwatch metric alarm."
  value       = try(aws_cloudwatch_metric_alarm.metric_alarm[0].arn, "")
}
