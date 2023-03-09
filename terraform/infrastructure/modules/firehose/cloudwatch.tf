resource "aws_cloudwatch_log_group" "firehose" {
  name              = "/aws/kinesisfirehose/${var.prefix}-firehose-${var.apitype}"
  retention_in_days = local.cloudwatch.retention.days
}

resource "aws_cloudwatch_log_stream" "firehose" {
  name           = "${var.prefix}-firehose-${var.apitype}"
  log_group_name = aws_cloudwatch_log_group.firehose.name
}
