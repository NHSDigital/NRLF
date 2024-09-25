output "account_name" {
  value = var.account_name
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
      name = local.pointers_table_name
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


output "auth_store" {
  value = local.auth_store_id
}

output "version" {
  value = data.external.current-info.result.version
}
