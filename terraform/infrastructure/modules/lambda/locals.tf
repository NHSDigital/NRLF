locals {
  lambda_timeout               = 30
  lambda_log_retention_in_days = 30
  api_type                     = split("/", var.parent_path)[1]
}
