########## Document Pointer ############

resource "aws_dynamodb_table" "document-pointer" {
  name         = "${local.prefix}--document-pointer"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "id"
  attribute {
    name = "id"
    type = "S"
  }
  attribute {
    name = "nhs_number"
    type = "S"
  }

  global_secondary_index {
    name            = "idx_nhs_number_by_id"
    hash_key        = "nhs_number"
    range_key       = "id"
    projection_type = "ALL"
  }
  server_side_encryption {
    enabled     = true
    kms_key_arn = aws_kms_key.document-pointer.arn
  }
}

resource "aws_iam_policy" "document-pointer__dynamodb-read" {
  name        = "${local.prefix}--document-pointer--dynamodb-read"
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
  name        = "${local.prefix}--document-pointer--dynamodb-write"
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

resource "aws_kms_key" "document-pointer" {
  description             = "Document types table KMS key"
  deletion_window_in_days = local.kms.deletion_window_in_days

}

resource "aws_kms_alias" "document-pointer" {
  name          = "alias/${local.prefix}--document-pointer"
  target_key_id = aws_kms_key.document-pointer.key_id
}


resource "aws_iam_policy" "document-pointer__kms-read-write" {
  name        = "${local.prefix}--document-pointer--kms-read-write"
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

########## Document Type ############

resource "aws_dynamodb_table" "document-type" {
  name         = "${local.prefix}--document-type"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "snomed_code"
  attribute {
    name = "snomed_code"
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


########## Auth ############

resource "aws_dynamodb_table" "auth" {
  name         = "${local.prefix}--auth"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "id"
  attribute {
    name = "id"
    type = "S"
  }

  server_side_encryption {
    enabled     = true
    kms_key_arn = aws_kms_key.auth.arn
  }
}

resource "aws_iam_policy" "auth__dynamodb-read" {
  name        = "${local.prefix}--auth--dynamodb-read"
  description = "Read the auth table"
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
          aws_kms_key.auth.arn
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
          "${aws_dynamodb_table.auth.arn}*"
        ]
      }
    ]
  })
}

resource "aws_iam_policy" "auth__dynamodb-write" {
  name        = "${local.prefix}--auth--dynamodb-write"
  description = "Write to the auth table"
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
          aws_kms_key.auth.arn
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
          "${aws_dynamodb_table.auth.arn}*"
        ]
      }
    ]
  })
}

resource "aws_kms_key" "auth" {
  description             = "auth table KMS key"
  deletion_window_in_days = local.kms.deletion_window_in_days

}

resource "aws_kms_alias" "auth" {
  name          = "alias/${local.prefix}--auth"
  target_key_id = aws_kms_key.auth.key_id
}


resource "aws_iam_policy" "auth__kms-read-write" {
  name        = "${local.prefix}--auth--kms-read-write"
  description = "Encrypt and decrypt with the auth kms key"
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
          aws_kms_key.auth.arn
        ]
      }
    ]
  })
}
