resource "aws_iam_policy" "kms-read-write" {
  name        = "${var.prefix}--${var.name}--kms-read-write"
  description = "Encrypt and decrypt with the kms key"
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
          aws_kms_key.kms_key.arn
        ]
      }
    ]
  })
}

data "aws_iam_policy_document" "kms_default_policy" {
  statement {
    principals {
      type = "AWS"

      identifiers = [
        "arn:aws:iam::${local.aws_account_id}:root",
      ]
    }

    actions = [
      "kms:*",
    ]

    resources = [
      "*"
    ]

    sid = "Enable IAM User Permissions"
  }
}
