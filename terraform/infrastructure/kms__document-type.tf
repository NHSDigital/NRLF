resource "aws_kms_key" "document-type" {
  description             = "Document types table KMS key"
  deletion_window_in_days = local.kms.deletion_window_in_days

}

resource "aws_kms_alias" "document-type" {
  name          = "alias/${local.prefix}--document-type"
  target_key_id = aws_kms_key.document-type.key_id
}


resource "aws_iam_policy" "document-type__kms-read-write" {
  name        = "${local.prefix}--document-type--kms-read-write"
  description = "Encrypt and decrypt with the document-type kms key"
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
          aws_kms_key.document-type.arn
        ]
      }
    ]
  })
}
