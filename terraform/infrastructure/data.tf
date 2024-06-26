data "aws_caller_identity" "current" {}

data "aws_s3_object" "api-truststore-certificate" {
    bucket = "${local.shared_prefix}-api-truststore"
    key    = "certificates.pem"
}

data "aws_s3_bucket" "authorization-store" {
    count  = local.use_shared_resources ? 1 : 0
    bucket = "${local.prefix}-authorization-store"
}