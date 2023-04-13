resource "aws_s3_bucket" "firehose" {
  bucket        = "${var.prefix}-firehose"
  force_destroy = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "firehose" {
  bucket = aws_s3_bucket.firehose.id
  rule {
    apply_server_side_encryption_by_default {
      kms_master_key_id = aws_kms_key.firehose.arn
      sse_algorithm     = "aws:kms"
    }
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "firehose" {
  bucket = aws_s3_bucket.firehose.id

  rule {
    id     = "FirehoseLifecycle"
    status = "Enabled"

    transition {
      days          = local.s3.transition_storage.infrequent_access.days
      storage_class = local.s3.transition_storage.infrequent_access.storage_class
    }
    transition {
      days          = local.s3.transition_storage.glacier.days
      storage_class = local.s3.transition_storage.glacier.storage_class
    }
    expiration {
      days = local.s3.expiration.days
    }
  }
}

resource "aws_s3_bucket_acl" "firehose" {
  bucket = aws_s3_bucket.firehose.id
  acl    = "private"
}
