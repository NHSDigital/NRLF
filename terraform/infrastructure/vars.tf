variable "account_name" {
  type = string
}

variable "assume_role_arn" {
  type      = string
  sensitive = true
}

# What domain should the APIs be hosted under
variable "domain" {
  type = string
}

# TODO - Remove default once all environments are on new domain structure
variable "public_domain" {
  type    = string
  default = ""
}

# TODO - Remove default once all environments are on new domain structure
variable "public_sandbox_domain" {
  type    = string
  default = ""
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
