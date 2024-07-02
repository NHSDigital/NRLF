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

variable "public_domain" {
  type        = string
  description = "The public domain for the persistent environment"
}

variable "public_sandbox_domain" {
  type        = string
  description = "The public domain for the sandbox environment (optional)"
  nullable    = true
  default     = null
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

variable "use_shared_resources" {
  type    = bool
  default = false
}
