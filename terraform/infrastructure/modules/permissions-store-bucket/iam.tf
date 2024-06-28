resource "aws_iam_policy" "read-s3-authorization-store" {
  name        = "${var.name_prefix}-read-s3-authorization-store"
  description = "Read the authorization store S3 bucket"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "s3:GetObject",
          "s3:ListBucket",
        ]
        Effect = "Allow"
        Resource = [
          aws_s3_bucket.authorization-store.arn
        ]
      },
    ]
  })
}
