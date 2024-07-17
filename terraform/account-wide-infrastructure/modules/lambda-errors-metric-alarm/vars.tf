variable "evaluation_periods" {
  description = "The number of periods over which data is compared to the specified threshold."
  type        = number
}

variable "threshold" {
  description = "The value against which the specified statistic is compared."
  type        = number
  default     = null
}

variable "period" {
  description = "The period in seconds over which the specified statistic is applied."
  type        = string
  default     = null
}

variable "name_prefix" {
  type        = string
  description = "The prefix to apply to all resources in the module."
}

variable "kms_deletion_window_in_days" {
  type        = number
  description = "The duration in days after which the key is deleted after destruction of the resource."
  default     = 7
}
