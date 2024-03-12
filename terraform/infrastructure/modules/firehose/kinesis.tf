

resource "aws_kinesis_firehose_delivery_stream" "firehose" {
  name        = "${var.prefix}--cloudwatch-delivery-stream"
  destination = var.destination
  dynamic "splunk_configuration" {
    # "splunk_configuration" is only enabled if the below secret has been set by hand in the AWS Console
    #
    # NB: the for_each will not run in the case that 'secret_string' has not been set in the AWS Console, and
    # therefore this block will be omitted for default deployments (e.g. developer and CI workspaces).
    #
    # "dummyKey" is required because terraform can't for_each over arrays of values, only over key-value pairs in an object.
    # "dummyKey" is therefore an unused dummy key pointing to the splunk config secret
    for_each = { for item in data.aws_secretsmanager_secret_version.splunk_configuration.*.secret_string : "dummyKey" => jsondecode(item) }
    content {
      hec_endpoint               = "https://${splunk_configuration.value["nhs_splunk_url"]}/services/collector/event"
      hec_token                  = splunk_configuration.value["hec_token"]
      hec_acknowledgment_timeout = 300
      hec_endpoint_type          = "Event"     # Formatted as per https://docs.splunk.com/Documentation/Splunk/latest/Data/FormateventsforHTTPEventCollector
      s3_backup_mode             = "AllEvents" # Save to prefix "processed" or "errors" before forwarding to Splunk

      retry_duration = 0

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

      s3_configuration {
        role_arn            = aws_iam_role.firehose.arn
        prefix              = "splunk_backup/${local.s3_configuration.prefix}"
        error_output_prefix = local.s3_configuration.error_output_prefix
        bucket_arn          = aws_s3_bucket.firehose.arn
        buffering_size      = local.s3_configuration.buffer_size
        buffering_interval  = local.s3_configuration.buffer_interval
        compression_format  = local.s3_configuration.compression_format

      }
    }
  }



  dynamic "extended_s3_configuration" {
    # "extended_s3_configuration" runs INSTEAD OF splunk_configuration, intended for developer and CI
    # workspaces without logs being forwarded to Splunk
    #
    # NB: the for_each will *only* run in the case that 'secret_string' has not been set in the AWS Console, and
    # therefore this block will be *included* only for default deployments (e.g. developer and CI workspaces).
    for_each = length(data.aws_secretsmanager_secret_version.splunk_configuration.*.secret_string) == 0 ? toset([1]) : toset([]) # On : Off
    content {
      role_arn            = aws_iam_role.firehose.arn
      prefix              = "processed/${local.s3_configuration.prefix}"
      error_output_prefix = local.s3_configuration.error_output_prefix
      bucket_arn          = aws_s3_bucket.firehose.arn
      buffering_size      = local.s3_configuration.buffer_size
      buffering_interval  = local.s3_configuration.buffer_interval
      compression_format  = local.s3_configuration.compression_format
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
}
