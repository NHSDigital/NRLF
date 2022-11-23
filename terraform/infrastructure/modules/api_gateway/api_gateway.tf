resource "aws_api_gateway_rest_api" "api_gateway_rest_api" {
  name        = "${var.prefix}--${var.apitype}"
  description = "Manages an API Gateway Rest API."
  body = templatefile("${path.module}/../../../../api/${var.apitype}/swagger.yaml", merge(var.lambdas, {
    lambda_invoke_arn   = var.authoriser_lambda_invoke_arn,
    authoriser_iam_role = aws_iam_role.api_authorizer.arn,
    authoriser_name     = "${var.prefix}--${var.apitype}-authorizer"
  }))
}

resource "aws_api_gateway_deployment" "api_gateway_deployment" {
  rest_api_id = aws_api_gateway_rest_api.api_gateway_rest_api.id

  triggers = {
    redeployment = sha1(jsonencode(aws_api_gateway_rest_api.api_gateway_rest_api.body))
  }

  lifecycle {
    create_before_destroy = true
  }

  depends_on = [
    aws_api_gateway_rest_api.api_gateway_rest_api
  ]
}

resource "aws_api_gateway_stage" "api_gateway_stage" {
  deployment_id = aws_api_gateway_deployment.api_gateway_deployment.id
  rest_api_id   = aws_api_gateway_rest_api.api_gateway_rest_api.id
  stage_name    = "production"

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_gateway_access_logs.arn
    format = jsonencode({
      requestid : "$context.requestId",
      ip : "$context.identity.sourceIp",
      user_agent : "$context.identity.userAgent",
      request_time : "$context.requestTime",
      http_method : "$context.httpMethod",
      path : "$context.path",
      status : "$context.status",
      protocol : "$context.protocol",
      response_length : "$context.responseLength",
      x_correlationid : "$context.authorizer.x-correlation-id",
      nhsd_correlationid : "$context.authorizer.nhsd-correlation-id"
      environment : terraform.workspace
    })
  }

  depends_on = [
    aws_api_gateway_deployment.api_gateway_deployment,
    aws_api_gateway_rest_api.api_gateway_rest_api,
    aws_cloudwatch_log_group.api_gateway_access_logs
  ]
}

resource "aws_api_gateway_method_settings" "api_gateway_method_settings" {
  rest_api_id = aws_api_gateway_rest_api.api_gateway_rest_api.id
  stage_name  = aws_api_gateway_stage.api_gateway_stage.stage_name
  method_path = "*/*"
  settings {
    logging_level      = "ERROR"
    data_trace_enabled = true
  }

  depends_on = [
    aws_api_gateway_rest_api.api_gateway_rest_api,
    aws_api_gateway_stage.api_gateway_stage
  ]
}
