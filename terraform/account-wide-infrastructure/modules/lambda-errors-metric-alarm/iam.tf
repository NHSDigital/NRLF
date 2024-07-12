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
          aws_kms_key.lambda-errors-topic-key.arn
        ]
      }
    ]
  })
}
