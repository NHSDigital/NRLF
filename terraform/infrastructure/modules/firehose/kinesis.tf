

locals {
  splunk_configuration = jsondecode(data.aws_secretsmanager_secret_version.splunk_configuration.secret_string)
  hec_endpoint         = "https://${local.splunk_configuration["nhs_splunk_url"]}/services/collector/event"
  hec_token            = local.splunk_configuration["hec_token"]
}

resource "aws_kinesis_firehose_delivery_stream" "firehose" {
  name        = "${var.prefix}--cloudwatch-delivery-stream"
  destination = var.destination

  splunk_configuration {
    hec_endpoint               = local.hec_endpoint
    hec_token                  = local.hec_token
    hec_acknowledgment_timeout = 300
    hec_endpoint_type          = "Event"
    s3_backup_mode             = "FailedEventsOnly"
    retry_duration             = 0

    processing_configuration {
      enabled = "true"

      processors {
        type = "Decompression"
        parameters {
          parameter_name  = "CompressionFormat"
          parameter_value = "GZIP"
        }
      }

      processors {
        type = "CloudWatchLogProcessing"

        parameters {
          parameter_name  = "DataMessageExtraction"
          parameter_value = "true"
        }
      }
    }

    cloudwatch_logging_options {
      enabled         = true
      log_group_name  = aws_cloudwatch_log_group.firehose.name
      log_stream_name = aws_cloudwatch_log_stream.firehose.name
    }

    s3_configuration {
      role_arn            = aws_iam_role.firehose.arn
      prefix              = "processing-failed/${local.s3_configuration.prefix}"
      error_output_prefix = local.s3_configuration.error_output_prefix
      bucket_arn          = aws_s3_bucket.firehose.arn
      buffering_size      = local.s3_configuration.buffer_size
      buffering_interval  = local.s3_configuration.buffer_interval
      compression_format  = local.s3_configuration.compression_format
    }
  }
}
