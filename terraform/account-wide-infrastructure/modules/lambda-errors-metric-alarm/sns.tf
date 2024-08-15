resource "aws_sns_topic" "sns_topic" {
  name              = "${var.name_prefix}--lambda-errors-sns-topic"
  kms_master_key_id = aws_kms_key.lambda-errors-topic-key.key_id
}

resource "aws_sns_topic_subscription" "sns_subscription" {
  for_each  = nonsensitive(toset(tolist(jsondecode(data.aws_secretsmanager_secret_version.emails.secret_string))))
  topic_arn = aws_sns_topic.sns_topic.arn
  protocol  = "email"
  endpoint  = sensitive(each.value)
}
