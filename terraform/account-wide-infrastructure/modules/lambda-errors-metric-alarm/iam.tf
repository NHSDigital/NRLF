resource "aws_iam_policy" "lambda-errors-topic-kms-read-write" {
  name        = "${var.name_prefix}-lambda-errors-topic-kms-read-write"
  description = "Encrypt and decrypt with the lambda errors sns topic kms key"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "kms:Decrypt",
          "kms:DescribeKey",
          "kms:Encrypt",
          "kms:GenerateDataKey"
        ]
        Effect = "Allow"
        Resource = [
          aws_kms_key.lambda-errors-topic-key.arn,
          aws_cloudwatch_metric_alarm.metric_alarm.arn
        ]
      }
    ]
  })
}

data "aws_caller_identity" "current" {}

data "aws_iam_policy_document" "sns_kms_key_policy" {
  policy_id = "CloudWatchEncryptUsingKey"

  statement {
    effect = "Allow"
    actions = [
      "kms:*"
    ]
    resources = ["*"]

    principals {
      type        = "AWS"
      identifiers = ["arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"]
    }
  }

  statement {
    effect = "Allow"
    actions = [
      "kms:Decrypt",
      "kms:GenerateDataKey"
    ]
    resources = ["*"]

    principals {
      type        = "Service"
      identifiers = ["cloudwatch.amazonaws.com"]
    }
  }
}
