resource "aws_sns_topic" "sns_topic" {
  name = "${var.prefix}--${var.name}"
}

resource "aws_sns_topic_subscription" "sns_subscription" {
  topic_arn = aws_sns_topic.sns_topic.arn
  protocol  = var.protocol
  endpoint  = var.endpoint
}
