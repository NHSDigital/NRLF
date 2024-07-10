variable "prefix" {}

variable "name" {}

variable "protocol" {
  description = "Used to define the protocol for the sns subscription."
  type        = string
  default     = "email"
}
