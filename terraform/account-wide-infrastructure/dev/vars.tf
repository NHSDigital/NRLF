variable "assume_account" {
  sensitive = true
}

variable "assume_role" {}

variable "dev_api_domain_name" {
  description = "The internal DNS name of the API Gateway for the dev environment"
  default     = "dev.api.record-locator.dev.national.nhs.uk"
}

variable "devsandbox_api_domain_name" {
  description = "The internal DNS name of the API Gateway for the dev environment"
  default     = "dev-sandbox.api.record-locator.dev.national.nhs.uk"
}
