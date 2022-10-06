resource "aws_kms_key" "document-reference" {
  description             = "Document reference table KMS key"
  deletion_window_in_days = local.kms.deletion_window_in_days

}

resource "aws_kms_alias" "document-reference" {
  name          = "alias/${local.prefix}--document-reference"
  target_key_id = aws_kms_key.document-reference.key_id
}


resource "aws_iam_policy" "document-reference__kms-read-write" {
  name        = "${local.prefix}--document-reference--kms-read-write"
  description = "Encrypt and decrypt with the document-reference kms key"
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
          aws_kms_key.document-reference.arn
        ]
      }
    ]
  })
}
