variable "prefix" {}

variable "apitype" {}

variable "lambdas" {}

variable "kms_key_id" {}

variable "authoriser_lambda_invoke_arn" {}

variable "authoriser_lambda_arn" {}

variable "domain" {
  type = string
}

variable "path" {
  type = string
}

variable "capability_statement_content" {
  type = string
}
