variable "name_prefix" {
  type        = string
  description = "The prefix to apply to all resources in the module."
}

variable "enable_deletion_protection" {
  type        = bool
  description = "Enable deletion protection for the DynamoDB table."
  default     = false
}

variable "enable_pitr" {
  type        = bool
  description = "Enable point-in-time recovery for the DynamoDB table."
  default     = false
}

variable "kms_deletion_window_in_days" {
  type        = number
  description = "The duration in days after which the key is deleted after destruction of the resource."
  default     = 7
}
