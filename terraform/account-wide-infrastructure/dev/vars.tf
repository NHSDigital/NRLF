variable "assume_account" {
  sensitive = true
}

variable "assume_role" {}

variable "dev_api_domain_name" {
  description = "The internal DNS name of the API Gateway for the dev environment"
  default     = "api.dev.record-locator.national.nhs.uk"
}
