resource "aws_lambda_function" "lambda_function" {
  function_name    = "${var.prefix}--sandbox-seeder"
  runtime          = "python3.9"
  handler          = "cron.seed_sandbox.index.handler"
  role             = aws_iam_role.lambda_role.arn
  filename         = "${path.module}/../../../../cron/seed_sandbox/dist/seed_sandbox.zip"
  source_code_hash = filebase64sha256("${path.module}/../../../../cron/seed_sandbox/dist/seed_sandbox.zip")
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
