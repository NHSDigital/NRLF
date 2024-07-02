
variable "domain_zone" {
  description = "The Route53 zone ID for the domain"
  type        = string
}

variable "subject_alternative_names" {
  description = "The subject alternative names for the certificate"
  type        = list(any)
  default     = []
}

variable "domain_name" {
  description = "The internal DNS name of the API Gateway for the dev environment"
  type        = string
}

variable "mtls_certificate_file" {
  description = "The path to the mtls certificate file"
  type        = string
}
