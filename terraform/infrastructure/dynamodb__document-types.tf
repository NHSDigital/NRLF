resource "aws_dynamodb_table" "document-types" {
  name           = "${local.prefix}--document-types"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "nhs_number"
  attribute {
    name = "nhs_number"
    type = "S"
  }
  server_side_encryption {
    enabled = true
    kms_key_arn = aws_kms_key.document-types.arn
  }
}

resource "aws_iam_policy" "document-types__dynamodb-read" {
  name = "${local.prefix}--document-types--dynamodb-read"
  description = "Read the document-types table"
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
          aws_kms_key.document-types.arn
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
          "${aws_dynamodb_table.document-types.arn}*"
        ]
      }
    ]
  })
}

resource "aws_iam_policy" "document-types__dynamodb-write" {
  name = "${local.prefix}--document-types--dynamodb-write"
  description = "Write to the document-types table"
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
          aws_kms_key.document-types.arn
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
          "${aws_dynamodb_table.document-types.arn}*"
        ]
      }
    ]
  })
}
