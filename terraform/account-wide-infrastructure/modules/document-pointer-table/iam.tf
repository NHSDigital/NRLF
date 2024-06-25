resource "aws_iam_policy" "document-pointer__dynamodb-read" {
  name        = "${var.name_prefix}--document-pointer--dynamodb-read"
  description = "Read the document-pointer table"
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
          aws_kms_key.document-pointer.arn
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
          "${aws_dynamodb_table.document-pointer.arn}*"
        ]
      }
    ]
  })
}

resource "aws_iam_policy" "document-pointer__dynamodb-write" {
  name        = "${var.name_prefix}--document-pointer--dynamodb-write"
  description = "Write to the document-pointer table"
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
          aws_kms_key.document-pointer.arn
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
          "${aws_dynamodb_table.document-pointer.arn}*"
        ]
      }
    ]
  })
}

resource "aws_iam_policy" "document-pointer__kms-read-write" {
  name        = "${var.name_prefix}--document-pointer--kms-read-write"
  description = "Encrypt and decrypt with the document-pointer kms key"
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
          aws_kms_key.document-pointer.arn
        ]
      }
    ]
  })
}
