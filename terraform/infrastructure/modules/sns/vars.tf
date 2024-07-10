variable "prefix" {}

variable "name" {}

variable "protocol" {
  description = "Used to define the protocol for the sns subscription."
  type        = string
  default     = "email"
}

variable "endpoint" {
  description = "Used to define the endpoint for the sns subscription to which it sends the events."
  type        = string
  default     = ""
}
