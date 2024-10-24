output "delivery_stream" {
  value = {
    arn = aws_kinesis_firehose_delivery_stream.firehose.arn
    s3 = {
      # By concatenating the extended_s3_configuration and s3_configuration we get the S3 bucket data in either the case
      # that we've enabled Splunk (persistent environments) or not enabled Splunk (developer and CI workspaces)
      arn          = aws_kinesis_firehose_delivery_stream.firehose.splunk_configuration[0].s3_configuration.*.bucket_arn
      prefix       = aws_kinesis_firehose_delivery_stream.firehose.splunk_configuration[0].s3_configuration.*.prefix
      error_prefix = aws_kinesis_firehose_delivery_stream.firehose.splunk_configuration[0].s3_configuration.*.error_output_prefix
    }
  }
}

output "splunk" {
  value = {
    index = var.splunk_index
  }
}

output "firehose_subscription" {
  value = {
    destination = {
      arn = aws_kinesis_firehose_delivery_stream.firehose.arn
    }
    role = {
      arn = aws_iam_role.firehose_subscription.arn
    }
    filter = {
      # At least two items, and the first not any of INIT_START, START, END, REPORT
      pattern = "[first_item_on_this_log_line != \"INIT_START\" && first_item_on_this_log_line != \"START\" && first_item_on_this_log_line != \"END\" && first_item_on_this_log_line != \"REPORT\", everything_else_on_this_log_line]"
    }
  }
}
