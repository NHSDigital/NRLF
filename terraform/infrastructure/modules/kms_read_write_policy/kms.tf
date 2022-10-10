resource "aws_kms_key" "kms_key" {
  description             = "${title(var.name)} table KMS key"
  deletion_window_in_days = local.kms.deletion_window_in_days

  #policy = data.aws_iam_policy_document.policy_document.json

}

resource "aws_kms_alias" "kms_alias" {
  name          = "alias/${var.prefix}--${var.name}"
  target_key_id = aws_kms_key.kms_key.key_id

  depends_on = [
    aws_kms_key.kms_key
  ]
}