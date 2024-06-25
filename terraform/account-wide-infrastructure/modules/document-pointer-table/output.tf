output "document_pointer_table_name" {
  description = "Name of the document-pointer table"
  value       = aws_dynamodb_table.document-pointer.name
}

output "document_pointer_read_policy_arn" {
  description = "Policy to read from the document-pointer table"
  value       = aws_iam_policy.document-pointer__dynamodb-read.arn
}

output "document_pointer_write_policy_arn" {
  description = "Policy to write to the document-pointer table"
  value       = aws_iam_policy.document-pointer__dynamodb-write.arn
}
