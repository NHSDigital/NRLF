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
