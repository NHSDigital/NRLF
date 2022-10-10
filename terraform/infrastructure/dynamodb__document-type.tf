resource "aws_dynamodb_table" "document-type" {
  name           = "${local.prefix}--document-type"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "snomed_code"
  attribute {
    name = "snomed_code"
    type = "S"
  }
  server_side_encryption {
    enabled = true
    kms_key_arn = aws_kms_key.document-type.arn
  }
}

resource "aws_iam_policy" "document-type__dynamodb-read" {
  name = "${local.prefix}--document-type--dynamodb-read"
  description = "Read the document-type table"
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
          aws_kms_key.document-type.arn
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
          "${aws_dynamodb_table.document-type.arn}*"
        ]
      }
    ]
  })
}

resource "aws_iam_policy" "document-type__dynamodb-write" {
  name = "${local.prefix}--document-type--dynamodb-write"
  description = "Write to the document-type table"
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
          aws_kms_key.document-type.arn
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
          "${aws_dynamodb_table.document-type.arn}*"
        ]
      }
    ]
  })
}
