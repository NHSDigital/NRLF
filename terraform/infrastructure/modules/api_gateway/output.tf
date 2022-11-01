output "api_gateway_id" {
  value = aws_api_gateway_rest_api.api_gateway_rest_api.id
}

output "api_base_url" {
  value = aws_api_gateway_stage.api_gateway_stage.invoke_url
}
