output "pointers_table_name" {
  description = "Name of the pointers table"
  value       = aws_dynamodb_table.pointers.name
}

output "pointers_read_policy_arn" {
  description = "Policy to read from the pointers table"
  value       = aws_iam_policy.pointers-table-read.arn
}

output "pointers_write_policy_arn" {
  description = "Policy to write to the pointers table"
  value       = aws_iam_policy.pointers-table-write.arn
}
