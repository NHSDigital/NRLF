resource "aws_dynamodb_table" "consumer" {
  name           = "${local.prefix}--consumer"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "ods_code"
  attribute {
    name = "ods_code"
    type = "S"
  }
  server_side_encryption {
    enabled = true
    kms_key_arn = aws_kms_key.consumer.arn
  }
}

resource "aws_iam_policy" "consumer__dynamodb-read" {
  name = "${local.prefix}--consumer--dynamodb-read"
  description = "Read the consumer table"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "kms:Decrypt",
          "kms:DescribeKey"
        ]
        Effect = "Allow"
        Resource = [
          aws_kms_key.consumer.arn
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:Query",
          "dynamodb:Scan",
          "dynamodb:GetItem",
        ],
        Resource = [
          "${aws_dynamodb_table.consumer.arn}*"
        ]
      }
    ]
  })
}

resource "aws_iam_policy" "consumer__dynamodb-write" {
  name = "${local.prefix}--consumer--dynamodb-write"
  description = "Write to the consumer table"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "kms:Encrypt",
          "kms:GenerateDataKey"
        ]
        Effect = "Allow"
        Resource = [
          aws_kms_key.consumer.arn
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem",
        ],
        Resource = [
          "${aws_dynamodb_table.consumer.arn}*"
        ]
      }
    ]
  })
}
