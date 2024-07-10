resource "aws_sns_topic" "lambda_errors" {
  name = "${var.prefix}--${var.name}"
}

resource "aws_sns_topic_subscription" "email_subscription" {
  topic_arn = var.topic_arn
  protocol  = var.protocol
  endpoint  = var.endpoint
}
