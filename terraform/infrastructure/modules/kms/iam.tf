data "aws_iam_policy_document" "policy_document" {
  source_policy_documents = [
    data.aws_iam_policy_document.kms_default_policy.json
  ]
  statement {
    principals {
      type = "Service"

      identifiers = [
        "logs.eu-west-2.amazonaws.com"
      ]
    }
    actions = [
      "kms:Encrypt*",
      "kms:Decrypt*",
      "kms:ReEncrypt*",
      "kms:GenerateDataKey*",
      "kms:Describe*"
    ]
    resources = ["*"]
    condition {
      test     = "ArnLike"
      variable = "kms:EncryptionContext:aws:logs:arn"
      values = [
        "arn:aws:logs:eu-west-2:${var.assume_account}:log-group:*"
      ]
    }
  }
}

data "aws_iam_policy_document" "kms_default_policy" {
  statement {
    principals {
      type = "AWS"

      identifiers = [
        "arn:aws:iam::${var.assume_account}:root",
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