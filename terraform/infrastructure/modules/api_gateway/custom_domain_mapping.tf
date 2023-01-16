resource "aws_api_gateway_base_path_mapping" "mapping" {
  api_id      = aws_api_gateway_rest_api.api_gateway_rest_api.id
  stage_name  = aws_api_gateway_stage.api_gateway_stage.stage_name
  domain_name = var.domain
  base_path   = var.path
  depends_on = [
    aws_api_gateway_stage.api_gateway_stage
  ]
}
