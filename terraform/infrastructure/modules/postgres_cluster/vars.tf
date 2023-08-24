variable "name" {}
variable "prefix" {}
variable "environment" {}
variable "region" {}
variable "cloudwatch_kms_arn" {}
variable "account_name" {}
variable "layers" {}
variable "schema_path" {}
variable "static_dimensions_path" {}
variable "assume_account" {}
variable "dynamodb_table" {}
variable "dynamodb_table_kms_key_arn" {}
variable "is_persistent_environment" {
  type    = bool
  default = false
}
