resource "aws_sns_topic" "sns_topic" {
  name = "${var.prefix}--${var.name}"
}

resource "aws_sns_topic_subscription" "sns_subscription" {
  for_each  = toset(["spine-cell-sigma-noti-aaaalor2u6funj7q3a4v7cpuba@nhsdigitalcorporate.org.slack.com", "eesa.mahmood1@nhs.net"])
  topic_arn = aws_sns_topic.sns_topic.arn
  protocol  = var.protocol
  endpoint  = each.value
}
