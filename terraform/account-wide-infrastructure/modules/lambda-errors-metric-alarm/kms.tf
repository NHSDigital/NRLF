resource "aws_kms_key" "lambda-errors-topic-key" {
  description             = "Lambda errors SNS topic table KMS key"
  deletion_window_in_days = var.kms_deletion_window_in_days
  policy                  = data.aws_iam_policy_document.sns_kms_key_policy.json

}

resource "aws_kms_alias" "lambda-errors-topic-alias" {
  name          = "alias/${var.name_prefix}-lambda-errors-topic-table-key"
  target_key_id = aws_kms_key.lambda-errors-topic-key.key_id
}
