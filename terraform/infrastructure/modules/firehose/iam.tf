
resource "aws_iam_role" "firehose" {
  name        = "${var.prefix}-firehose-${var.apitype}"
  description = "IAM Role for Kinesis Firehose"
  assume_role_policy = jsonencode({
    Version : "2012-10-17",
    Statement : [
      {
        Action : "sts:AssumeRole",
        Principal : { Service : "firehose.amazonaws.com" },
        Effect : "Allow",
        Sid : ""
      }
    ]
  })

}

data "aws_iam_policy_document" "firehose" {
  statement {
    actions = [
      "s3:AbortMultipartUpload",
      "s3:GetBucketLocation",
      "s3:GetObject",
      "s3:ListBucket",
      "s3:ListBucketMultipartUploads",
      "s3:PutObject",
    ]

    resources = [
      aws_s3_bucket.firehose.arn,
      "${aws_s3_bucket.firehose.arn}/*",
    ]
    effect = "Allow"
  }

  statement {
    actions = [
      "kms:DescribeKey",
      "kms:GenerateDataKey*",
      "kms:Encrypt",
      "kms:ReEncrypt*",
      "kms:Decrypt",
    ]

    resources = [
      aws_kms_key.firehose.arn,
    ]
  }
  statement {
    actions = [
      "kms:DescribeKey",
      "kms:Decrypt",
    ]

    resources = [
      "${var.cloudwatch_kms_arn}",
    ]
  }

  statement {
    actions = [
      "kms:ListAliases",
    ]

    resources = ["*"]
  }

  statement {
    actions = [
      "lambda:InvokeFunction",
      "lambda:GetFunctionConfiguration",
    ]

    resources = [
      "${module.lambda.arn}:$LATEST",
    ]
  }

  statement {
    actions = [
      "logs:PutLogEvents",
    ]
    resources = [
      aws_cloudwatch_log_group.firehose.arn,
      aws_cloudwatch_log_stream.firehose.arn
    ]
    effect = "Allow"
  }
}

resource "aws_iam_policy" "firehose" {
  name   = "${var.prefix}-firehose-${var.apitype}"
  policy = data.aws_iam_policy_document.firehose.json
}

resource "aws_iam_role_policy_attachment" "firehose" {
  role       = aws_iam_role.firehose.name
  policy_arn = aws_iam_policy.firehose.arn
}

resource "aws_iam_policy" "lambda" {
  name        = "${var.prefix}-firehose-lambda-${var.apitype}"
  description = "Read from any log, write to firehose, write to own logs"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "logs:GetLogEvents"
        ]
        Effect = "Allow"
        Resource = [
          "*",
        ]
      },
      {
        Action = [
          "firehose:PutRecordBatch",
        ],
        Effect = "Allow"
        Resource = [
          "${aws_kinesis_firehose_delivery_stream.firehose.arn}*"
        ]
      },
      {
        Action = [
          "logs:*",
        ]
        Effect = "Allow"
        Resource = [
          "${module.lambda.arn}:*",
        ]
      }
    ]
  })
}
