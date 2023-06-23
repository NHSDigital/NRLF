resource "aws_lambda_function" "lambda_function" {
  function_name    = substr("${var.prefix}--${replace(var.parent_path, "/", "--")}--${var.name}", 0, 64)
  runtime          = "python3.9"
  handler          = var.handler
  role             = aws_iam_role.lambda_role.arn
  filename         = "${path.module}/../../../../${var.parent_path}/${var.name}/dist/${var.name}.zip"
  source_code_hash = filebase64sha256("${path.module}/../../../../${var.parent_path}/${var.name}/dist/${var.name}.zip")
  timeout          = local.lambda_timeout
  memory_size      = 128

  environment {
    variables = merge(var.environment_variables, { "SOURCE" : "${var.prefix}--${replace(var.parent_path, "/", "--")}--${var.name}" })
  }

  layers = var.layers

  depends_on = [
    aws_iam_role.lambda_role
  ]

  dynamic "vpc_config" {
    for_each = length(var.vpc) > 0 ? toset([1]) : toset([])
    content {
      subnet_ids         = var.vpc.subnet_ids
      security_group_ids = var.vpc.security_group_ids
    }
  }
}


resource "aws_lambda_permission" "lambda_permission" {
  count         = length(var.api_gateway_source_arn)
  statement_id  = "AllowExecutionFromAPIGateway-${count.index}"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.lambda_function.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = var.api_gateway_source_arn[count.index]

  depends_on = [
    aws_lambda_function.lambda_function
  ]
}
