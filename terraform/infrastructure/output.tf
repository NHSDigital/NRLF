output "assume_account_id" {
  value     = var.assume_account
  sensitive = true
}

output "workspace" {
  value = terraform.workspace
}

output "prefix" {
  value = local.prefix
}

output "dynamodb" {
  value = {
    document_pointer = {
      name = aws_dynamodb_table.document-pointer.name
    }
  }
}

output "api_base_urls" {
  value = {
    producer = module.producer__gateway.api_base_url
  }
}
