variable "assume_account" {
  sensitive = true
}

variable "assume_role" {}

/*variable "prod_api_domain_name" {
  description = "The internal DNS name of the API Gateway for the prod environment"
  default     = "api.record-locator.national.nhs.uk"
}*/
