variable "prefix" {}

variable "region" {}

variable "layers" {}

variable "kms_key_id" {}

variable "environment_variables" {}

variable "additional_policies" {
  default = []
}
