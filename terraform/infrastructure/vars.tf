variable "assume_account" {
  sensitive = true
}

variable "assume_role" {}

# What domain should the APIs be hosted under
variable "domain" {
  type = string
}

# Use the root domain if the workspace name matches the following, otherwise use a subdomain
variable "subdomain_if_not_workspace" {
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
