output "assume_account_id" {
  value     = var.assume_account
  sensitive = true
}

output "account_name" {
  value = local.account_name
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
    consumer = module.consumer__gateway.api_base_url
  }
}

output "status_lambda_function_names" {
  value = {
    producer = module.producer__status.function_name
    consumer = module.consumer__status.function_name
  }
}

output "certificate_domain_name" {
  value = aws_acm_certificate.certificate.domain_name
}

# output "firehose" {
#   value = {
#     processor = module.firehose__processor
#   }
# }

output "mi" {
  value = module.mi
}

output "auth_store" {
  value = aws_s3_bucket.authorization-store.id
}
