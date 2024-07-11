resource "aws_sns_topic" "sns_topic" {
  name = "${var.name_prefix}--lambda-errors-sns-topic"
}

resource "aws_sns_topic_subscription" "sns_subscription" {
  for_each  = toset(data.aws_secretsmanager_secret_version.emails.secret_string)
  topic_arn = aws_sns_topic.sns_topic.arn
  protocol  = "email"
  endpoint  = each.value
}
