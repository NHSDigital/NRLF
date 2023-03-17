resource "aws_kinesis_firehose_delivery_stream" "firehose" {
  name        = "${var.prefix}-cloudwatch-to-splunk-${var.apitype}"
  destination = "extended_s3"

  extended_s3_configuration {
    role_arn = aws_iam_role.firehose.arn

    # Note could add partition key info to prefix to help debug, requires more investigation
    prefix              = "processed/!{timestamp:yyyy}/!{timestamp:MM}/!{timestamp:dd}/!{timestamp:HH}/"
    error_output_prefix = "errors/!{timestamp:yyyy}/!{timestamp:MM}/!{timestamp:dd}/!{timestamp:HH}/!{firehose:error-output-type}/"
    bucket_arn          = aws_s3_bucket.firehose.arn
    buffer_size         = 5
    buffer_interval     = 300
    compression_format  = "GZIP"

    processing_configuration {
      enabled = "true"

      processors {
        type = "Lambda"

        parameters {
          parameter_name  = "LambdaArn"
          parameter_value = "${module.lambda.arn}:$LATEST"
        }
        parameters {
          parameter_name  = "RoleArn"
          parameter_value = aws_iam_role.firehose.arn
        }
      }
    }

    cloudwatch_logging_options {
      enabled         = true
      log_group_name  = aws_cloudwatch_log_group.firehose.name
      log_stream_name = aws_cloudwatch_log_stream.firehose.name
    }
  }
}
