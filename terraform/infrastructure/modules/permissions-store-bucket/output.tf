output "bucket_arn" {
  description = "Name of the authorization store S3 bucket"
  value       = aws_s3_bucket.authorization-store.arn
}

output "bucket_id" {
  description = "Name of the authorization store S3 bucket"
  value       = aws_s3_bucket.authorization-store.id
}

output "bucket_read_policy_arn" {
  description = "Policy to read from the authorization store S3 bucket"
  value       = aws_iam_policy.read-s3-authorization-store.arn
}