resource "aws_cloudwatch_log_group" "api_gateway_access_logs" {
  name = "/aws/api-gateway/access-logs/${aws_api_gateway_rest_api.api_gateway_rest_api.name}"

  kms_key_id = var.kms_key_id

  depends_on = [
    aws_api_gateway_rest_api.api_gateway_rest_api
  ]

}

resource "aws_cloudwatch_log_group" "api_gateway_execution_logs" {
  name = "API-Gateway-Execution-Logs_${aws_api_gateway_rest_api.api_gateway_rest_api.id}/production"

  kms_key_id = var.kms_key_id

  depends_on = [
    aws_api_gateway_rest_api.api_gateway_rest_api
  ]

}
