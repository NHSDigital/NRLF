output "bucket_arn" {
  description = "Name of the truststore S3 bucket"
  value       = aws_s3_bucket.api_truststore.arn
}

output "certificates_object_arn" {
  description = "ARN of the truststore certificates object"
  value       = aws_s3_object.api_truststore_certificate.arn
}
