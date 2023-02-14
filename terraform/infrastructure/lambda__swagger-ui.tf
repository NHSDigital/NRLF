resource "aws_lambda_function" "swagger-ui" {
  function_name    = "${local.prefix}--swagger-ui"
  runtime          = "nodejs16.x"
  handler          = "index.handler"
  role             = aws_iam_role.swagger-ui.arn
  filename         = "../../lambdas/nrl-swagger-ui/dist/swagger-ui.zip"
  source_code_hash = filebase64sha256("../../lambdas/nrl-swagger-ui/dist/swagger-ui.zip")
  timeout          = local.lambda_timeout
  memory_size      = 128

  depends_on = [
    aws_iam_role.swagger-ui
  ]
}

resource "aws_cloudwatch_log_group" "lambda_cloudwatch_log_group" {
  name              = "/aws/lambda/${aws_lambda_function.swagger-ui.function_name}"
  retention_in_days = local.lambda_log_retention_in_days
}


resource "aws_lambda_function_url" "swagger-ui" {
  function_name      = aws_lambda_function.swagger-ui.function_name
  authorization_type = "NONE"
}

resource "aws_iam_role" "swagger-ui" {
  name = "${local.prefix}--swagger-ui"
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

resource "aws_iam_role_policy_attachment" "swagger-ui_lambda-execution" {
  role       = aws_iam_role.swagger-ui.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"

  depends_on = [
    aws_iam_role.swagger-ui
  ]
}

output "swagger-ui_url" {
  value = aws_lambda_function_url.swagger-ui.function_url
}
