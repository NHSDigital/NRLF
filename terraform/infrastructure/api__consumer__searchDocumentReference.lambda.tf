# ------------------------------------------------------------------------------
# consumer - searchDocumentReference
# ------------------------------------------------------------------------------

resource "aws_iam_role" "consumer__searchDocumentReference__role" {
  name = substr("${local.prefix}--api--consumer--searchDocumentReference", 0, 64)
  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Principal = {
          Service = "lambda.amazonaws.com"
        },
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "consumer__searchDocumentReference__lambda-log" {
  role       = aws_iam_role.consumer__searchDocumentReference__role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_lambda_function" "consumer__searchDocumentReference" {
  function_name    = substr("${local.prefix}--api--consumer--searchDocumentReference", 0, 64)
  runtime          = "python3.9"
  handler          = "index.handler"
  role             = aws_iam_role.consumer__searchDocumentReference__role.arn
  filename         = "${path.module}/../../api/consumer/searchDocumentReference/dist/searchDocumentReference.zip"
  source_code_hash = filebase64sha256("${path.module}/../../api/consumer/searchDocumentReference/dist/searchDocumentReference.zip")
  timeout          = local.lambda_timeout
  memory_size      = 128
  environment {
    variables = {
      PREFIX = local.prefix
    }
  }
  layers = [
    aws_lambda_layer_version.nrlf.arn,
    aws_lambda_layer_version.lambda-utils.arn,
    aws_lambda_layer_version.third-party.arn
  ]
  depends_on = [
    aws_cloudwatch_log_group.consumer__searchDocumentReference__lambda-log
  ]
}

resource "aws_cloudwatch_log_group" "consumer__searchDocumentReference__lambda-log" {
  name              = "/aws/lambda/${substr("${local.prefix}--api--consumer--searchDocumentReference", 0, 64)}"
  retention_in_days = local.lambda_log_retention_in_days

  kms_key_id = aws_kms_key.cloudwatch.arn

}

resource "aws_lambda_permission" "consumer__searchDocumentReference__lambda-permission" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.consumer__searchDocumentReference.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "arn:aws:execute-api:${local.region}:${var.assume_account}:${aws_api_gateway_rest_api.consumer.id}/*/GET/DocumentReference"
}
