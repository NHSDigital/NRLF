data "aws_caller_identity" "current" {}

data "aws_s3_object" "api-truststore-certificate" {
    bucket = "${local.shared_prefix}-api-truststore"
    key    = "certificates.pem"
}
