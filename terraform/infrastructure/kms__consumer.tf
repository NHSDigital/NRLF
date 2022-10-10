resource "aws_kms_key" "consumer" {
  description             = "consumer table KMS key"
  deletion_window_in_days = local.kms.deletion_window_in_days

}

resource "aws_kms_alias" "consumer" {
  name          = "alias/${local.prefix}--consumer"
  target_key_id = aws_kms_key.consumer.key_id
}


resource "aws_iam_policy" "consumer__kms-read-write" {
  name        = "${local.prefix}--consumer--kms-read-write"
  description = "Encrypt and decrypt with the consumer kms key"
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
          aws_kms_key.consumer.arn
        ]
      }
    ]
  })
}
