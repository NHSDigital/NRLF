resource "aws_iam_policy" "pointers-table-read" {
  name        = "${var.name_prefix}-pointers-table-read"
  description = "Read the pointers-table"
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
          aws_kms_key.pointers-table-key.arn
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
          "${aws_dynamodb_table.pointers.arn}*"
        ]
      }
    ]
  })
}

resource "aws_iam_policy" "pointers-table-write" {
  name        = "${var.name_prefix}-pointers-table-write"
  description = "Write to the pointers-table"
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
          aws_kms_key.pointers-table-key.arn
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
          "${aws_dynamodb_table.pointers.arn}*"
        ]
      }
    ]
  })
}

resource "aws_iam_policy" "pointers-kms-read-write" {
  name        = "${var.name_prefix}-pointers-kms-read-write"
  description = "Encrypt and decrypt with the pointers table kms key"
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
          aws_kms_key.pointers-table-key.arn
        ]
      }
    ]
  })
}
