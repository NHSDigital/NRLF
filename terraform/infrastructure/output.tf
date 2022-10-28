output "aws_account_id" {
  value = var.assume_account
  sensitive = true
}

output "workspace" {
  value = terraform.workspace
}
