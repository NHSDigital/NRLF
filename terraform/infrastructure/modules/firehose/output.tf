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
      pattern = "[lambda_log_type != \"INIT_START\" && lambda_log_type != \"START\" && lambda_log_type != \"END\" && lambda_log_type != \"REPORT\", everything_else]"
    }
  }
}
