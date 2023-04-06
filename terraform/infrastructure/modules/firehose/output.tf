output "delivery_stream" {
  value = {
    arn = aws_kinesis_firehose_delivery_stream.firehose.arn
    s3 = {
      arn          = aws_kinesis_firehose_delivery_stream.firehose.extended_s3_configuration[0].bucket_arn
      prefix       = aws_kinesis_firehose_delivery_stream.firehose.extended_s3_configuration[0].prefix
      error_prefix = aws_kinesis_firehose_delivery_stream.firehose.extended_s3_configuration[0].error_output_prefix
    }
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
