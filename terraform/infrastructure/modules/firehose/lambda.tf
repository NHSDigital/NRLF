module "lambda" {
  source      = "../lambda"
  parent_path = "firehose"
  name        = "processor"
  region      = var.region
  prefix      = var.prefix
  layers      = var.layers
  kms_key_id  = var.cloudwatch_kms_arn
  environment_variables = {
    PREFIX      = "${var.prefix}--"
    ENVIRONMENT = var.environment
  }
  additional_policies = [
    aws_iam_policy.lambda.arn,
  ]
  handler = "firehose.processor.index.handler"
}

resource "aws_iam_policy" "lambda" {
  name        = "${var.prefix}-firehose-lambda"
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
