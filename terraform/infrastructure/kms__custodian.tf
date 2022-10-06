resource "aws_kms_key" "custodian" {
  description             = "Custodian table KMS key"
  deletion_window_in_days = local.kms.deletion_window_in_days

}

resource "aws_kms_alias" "custodian" {
  name          = "alias/${local.prefix}--custodian"
  target_key_id = aws_kms_key.custodian.key_id
}


resource "aws_iam_policy" "custodian__kms-read-write" {
  name        = "${local.prefix}--custodian--kms-read-write"
  description = "Encrypt and decrypt with the custodian kms key"
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
          aws_kms_key.custodian.arn
        ]
      }
    ]
  })
}
