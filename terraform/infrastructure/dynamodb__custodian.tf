resource "aws_dynamodb_table" "custodian" {
  name           = "${local.prefix}--custodian"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "ods_code"
  attribute {
    name = "ods_code"
    type = "S"
  }
  server_side_encryption {
    enabled = true
    kms_key_arn = aws_kms_key.custodian.arn
  }
}

resource "aws_iam_policy" "custodian__dynamodb-read" {
  name = "${local.prefix}--custodian--dynamodb-read"
  description = "Read the custodian table"
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
          aws_kms_key.custodian.arn
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
          "${aws_dynamodb_table.custodian.arn}*"
        ]
      }
    ]
  })
}

resource "aws_iam_policy" "custodian__dynamodb-write" {
  name = "${local.prefix}--custodian--dynamodb-write"
  description = "Write to the custodian table"
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
          aws_kms_key.custodian.arn
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
          "${aws_dynamodb_table.custodian.arn}*"
        ]
      }
    ]
  })
}
