variable "name_prefix" {
  type        = string
  description = "The prefix to apply to all resources in the module."
}

variable "server_certificate_file" {
  type        = string
  description = "The path to the server certificate file."
}

variable "enable_bucket_force_destroy" {
  type        = bool
  description = "A boolean flag to enable force destroy of the S3 bucket, so that all objects in the bucket are deleted when the bucket is destroyed."
  default     = false
}
