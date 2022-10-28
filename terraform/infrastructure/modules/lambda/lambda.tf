resource "aws_lambda_function" "lambda_function" {
  function_name    = substr("${var.prefix}--api--${var.apitype}--${var.name}", 0, 64)
  runtime          = "python3.9"
  handler          = var.handler
  role             = aws_iam_role.lambda_role.arn
  filename         = "${path.module}/../../../../api/${var.apitype}/${var.name}/dist/${var.name}.zip"
  source_code_hash = filebase64sha256("${path.module}/../../../../api/${var.apitype}/${var.name}/dist/${var.name}.zip")
  timeout          = local.lambda_timeout
  memory_size      = 128

  environment {
    variables = var.environment_variables
  }

  layers = var.layers

  depends_on = [
    aws_iam_role.lambda_role
  ]
}

resource "aws_lambda_permission" "lambda_permission" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.lambda_function.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = var.api_gateway_source_arn

  depends_on = [
    aws_lambda_function.lambda_function
  ]
}
