output "invoke_arn" {
  value = aws_lambda_function.lambda_function.invoke_arn
}

output "arn" {
  value = aws_lambda_function.lambda_function.arn
}

output "function_name" {
  value = aws_lambda_function.lambda_function.function_name
}

output "log_group_name" {
  value = aws_cloudwatch_log_group.lambda_cloudwatch_log_group.name
}

output "lambda_role_name" {
  value = aws_iam_role.lambda_role.name
}
