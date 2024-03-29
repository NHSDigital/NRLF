variable "account_name" {
  type = string
}

variable "assume_account" {
  sensitive = true
}

variable "assume_role" {}

# What domain should the APIs be hosted under
variable "domain" {
  type = string
}

variable "consumer_api_path" {
  type    = string
  default = "consumer"
}

variable "producer_api_path" {
  type    = string
  default = "producer"
}

variable "deletion_protection" {
  type    = bool
  default = false
}
