resource "aws_kms_key" "document-types" {
  description             = "Document types table KMS key"
  deletion_window_in_days = local.kms.deletion_window_in_days

}

resource "aws_kms_alias" "document-types" {
  name          = "alias/${local.prefix}--document-types"
  target_key_id = aws_kms_key.document-types.key_id
}


resource "aws_iam_policy" "document-types__kms-read-write" {
  name        = "${local.prefix}--document-types--kms-read-write"
  description = "Encrypt and decrypt with the document-types kms key"
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
          aws_kms_key.document-types.arn
        ]
      }
    ]
  })
}
