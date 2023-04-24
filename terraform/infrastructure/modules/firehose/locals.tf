locals {
  s3 = {
    transition_storage = {
      infrequent_access = {
        storage_class = "STANDARD_IA"
        days          = 150
      }
      glacier = {
        storage_class = "GLACIER"
        days          = 200
      }
    }

    expiration = {
      days = 1095
    }
  }

  cloudwatch = {
    retention = {
      days = 30
    }
  }

  s3_configuration = {
    # Note could add partition key info to prefix to help debug, requires more investigation
    prefix              = "!{timestamp:yyyy}/!{timestamp:MM}/!{timestamp:dd}/!{timestamp:HH}/"
    error_output_prefix = "errors/!{timestamp:yyyy}/!{timestamp:MM}/!{timestamp:dd}/!{timestamp:HH}/!{firehose:error-output-type}/"
    buffer_size         = 5
    buffer_interval     = 300
    compression_format  = "GZIP"
  }

}
