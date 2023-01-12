########## Document Type ############

resource "aws_dynamodb_table" "document-type" {
  name         = "${local.prefix}--document-type"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "pk"
  range_key    = "sk"

  attribute {
    name = "pk"
    type = "S"
  }

  attribute {
    name = "sk"
    type = "S"
  }

  server_side_encryption {
    enabled     = true
    kms_key_arn = aws_kms_key.document-type.arn
  }
}

resource "aws_iam_policy" "document-type__dynamodb-read" {
  name        = "${local.prefix}--document-type--dynamodb-read"
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
  name        = "${local.prefix}--document-type--dynamodb-write"
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
