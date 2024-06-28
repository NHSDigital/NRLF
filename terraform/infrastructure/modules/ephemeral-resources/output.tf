output "authorization_store_arn" {
  description = "Name of the authorization store S3 bucket"
  value       = module.ephemeral-s3-permission-store.bucket_arn
}

output "authorization_store_id" {
  description = "Id of the authorization store S3 bucket"
  value       = module.ephemeral-s3-permission-store.bucket_id
}

output "pointers_table_name" {
  description = "Name of the pointers dynamodb table"
  value       = module.ephemeral-pointers-table.table_name
}

output "pointers_table_read_policy_arn" {
  description = "Policy to read from the pointers table"
  value       = module.ephemeral-pointers-table.read_policy_arn
}

output "pointers_table_write_policy_arn" {
  description = "Policy to write to the pointers table"
  value       = module.ephemeral-pointers-table.write_policy_arn
}

output "pointers_kms_read_write_arn" {
  description = "Policy to encrypt and decrypt the pointers table with the kms key"
  value       = module.ephemeral-pointers-table.kms_read_write_policy_arn
}
