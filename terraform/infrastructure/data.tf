data "aws_caller_identity" "current" {}

data "aws_s3_object" "api-truststore-certificate" {
  bucket = "${local.shared_prefix}-api-truststore"
  key    = "certificates.pem"
}

data "aws_s3_bucket" "authorization-store" {
  count  = var.use_shared_resources ? 1 : 0
  bucket = "${local.shared_prefix}-authorization-store"
}

data "aws_dynamodb_table" "pointers-table" {
  count = var.use_shared_resources ? 1 : 0
  name  = "${local.shared_prefix}-pointers-table"
}

data "aws_iam_policy" "pointers-table-read" {
  count = var.use_shared_resources ? 1 : 0
  name  = "${local.shared_prefix}-pointers-table-read"
}

data "aws_iam_policy" "pointers-table-write" {
  count = var.use_shared_resources ? 1 : 0
  name  = "${local.shared_prefix}-pointers-table-write"
}

data "aws_iam_policy" "pointers-kms-read-write" {
  count = var.use_shared_resources ? 1 : 0
  name  = "${local.shared_prefix}-pointers-kms-read-write"
}
