variable "prefix" {}

variable "assume_account" {}

variable "region" {}

variable "layers" {}

variable "environment" {}

variable "cloudwatch_kms_arn" {}

variable "destination" {
  default = "extended_s3"
  type    = string
  validation {
    condition     = contains(["splunk", "extended_s3"], var.destination)
    error_message = "Valid value is one of the following: splunk, extended_s3."
  }
}

variable "splunk_index" {
  type    = string
  default = "aws_recordlocator_dev"
  validation {
    condition     = startswith(var.splunk_index, "aws_recordlocator_")
    error_message = "Splunk Index must start with aws_recordlocator_"
  }
}

variable "is_persistent_environment" {
  type    = bool
  default = false
}

variable "error_prefix" {
  type    = string
  default = "errors"
}
