resource "aws_iam_role" "firehose_subscription" {
  name        = "${var.prefix}-firehose-subscription-${var.apitype}"
  description = "Role for CloudWatch Log Group subscription"
  assume_role_policy = jsonencode({
    Version : "2012-10-17",
    Statement : [
      {
        Action : "sts:AssumeRole",
        Principal : { Service : "logs.eu-west-2.amazonaws.com" },
        Effect : "Allow",
        Sid : ""
      }
    ]
  })
}

data "aws_iam_policy_document" "firehose_subscription" {
  statement {
    actions = [
      "firehose:*",
    ]
    effect = "Allow"
    resources = [
      aws_kinesis_firehose_delivery_stream.firehose.arn,
    ]
  }
  statement {
    actions = [
      "iam:PassRole",
    ]
    effect = "Allow"
    resources = [
      aws_iam_role.firehose_subscription.arn
    ]
  }
}

resource "aws_iam_policy" "firehose_subscription" {
  name        = "${var.prefix}-firehose-subscription-${var.apitype}"
  description = "Cloudwatch to Firehose Subscription Policy"
  policy      = data.aws_iam_policy_document.firehose_subscription.json
}

resource "aws_iam_role_policy_attachment" "firehose_subscription" {
  role       = aws_iam_role.firehose_subscription.name
  policy_arn = aws_iam_policy.firehose_subscription.arn
}
