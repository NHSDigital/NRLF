resource "aws_kms_key" "firehose" {
}

resource "aws_kms_alias" "firehose" {
  name          = "alias/${var.prefix}-firehose-${var.apitype}"
  target_key_id = aws_kms_key.firehose.key_id
}
