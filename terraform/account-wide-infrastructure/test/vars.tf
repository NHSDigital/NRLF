variable "assume_account" {
  sensitive = true
}

variable "assume_role" {}

variable "qa_api_domain_name" {
  description = "The internal DNS name of the API Gateway for the QA environment"
  default     = "api.qa.record-locator.national.nhs.uk"
}

variable "qasandbox_api_domain_name" {
  description = "The internal DNS name of the API Gateway for the QA sandbox environment"
  default     = "api-sandbox.qa.record-locator.national.nhs.uk"
}

variable "int_api_domain_name" {
  description = "The internal DNS name of the API Gateway for the int environment"
  default     = "int.api.record-locator.int.national.nhs.uk"
}

variable "intsandbox_api_domain_name" {
  description = "The internal DNS name of the API Gateway for the int sandbox environment"
  default     = "int-sandbox.api.record-locator.int.national.nhs.uk"
}

variable "ref_api_domain_name" {
  description = "The internal DNS name of the API Gateway for the ref environment"
  default     = "ref.api.record-locator.ref.national.nhs.uk"
}
