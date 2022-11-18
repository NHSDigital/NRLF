output "invoke_arn" {
  value = aws_lambda_function.lambda_function.invoke_arn
}

output "arn" {
  value = aws_lambda_function.lambda_function.arn
}
