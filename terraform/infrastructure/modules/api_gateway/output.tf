output "api_gateway_id" {
  value = aws_api_gateway_rest_api.api_gateway_rest_api.id
}

output "api_base_url" {
  value = "https://${var.domain}/${var.path}"
}
