output "sns_topic_arn" {
  description = "ARN"
  value       = aws_sns_topic.lambda_errors.arn
}
