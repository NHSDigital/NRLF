output "authorization_store_arn" {
  description = "Name of the authorization store S3 bucket"
  value       = aws_s3_bucket.authorization-store.arn
}

output "authorization_store_id" {
  description = "Id of the authorization store S3 bucket"
  value       = aws_s3_bucket.authorization-store.id
}