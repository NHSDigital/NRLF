resource "aws_kms_key" "producer" {
  description             = "producer table KMS key"
  deletion_window_in_days = local.kms.deletion_window_in_days

}

resource "aws_kms_alias" "producer" {
  name          = "alias/${local.prefix}--producer"
  target_key_id = aws_kms_key.producer.key_id
}


resource "aws_iam_policy" "producer__kms-read-write" {
  name        = "${local.prefix}--producer--kms-read-write"
  description = "Encrypt and decrypt with the producer kms key"
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
          aws_kms_key.producer.arn
        ]
      }
    ]
  })
}
