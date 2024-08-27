variable "prefix" {}

variable "apitype" {}

variable "lambdas" {}

variable "kms_key_id" {}

variable "domain" {
  type = string
}

variable "path" {
  type = string
}

variable "capability_statement_content" {
  type = string
}

variable "retention" {
  default = 90
  type    = number
}
