resource "aws_kms_key" "cloudwatch" {
  description             = "Cloudwatch log KMS key"
  deletion_window_in_days = local.kms.deletion_window_in_days

  policy = data.aws_iam_policy_document.cloudwatch.json

}

resource "aws_kms_alias" "cloudwatch" {
  name          = "alias/${local.prefix}--cloudwatch"
  target_key_id = aws_kms_key.cloudwatch.key_id
}




data "aws_iam_policy_document" "cloudwatch" {
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
