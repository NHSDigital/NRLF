resource "aws_api_gateway_rest_api" "api_gateway_rest_api" {
  name                         = "${var.prefix}--${var.apitype}"
  description                  = "Manages an API Gateway Rest API."
  disable_execute_api_endpoint = true
  body = templatefile("${path.module}/../../../../api/${var.apitype}/swagger.yaml", merge(var.lambdas, {
    lambda_invoke_arn   = var.authoriser_lambda_invoke_arn,
    authoriser_iam_role = aws_iam_role.api_authorizer.arn,
    authoriser_name     = "${var.prefix}--${var.apitype}-authorizer"
  }))
}

resource "aws_api_gateway_deployment" "api_gateway_deployment" {
  rest_api_id = aws_api_gateway_rest_api.api_gateway_rest_api.id

  triggers = {
    redeployment    = sha1(jsonencode(aws_api_gateway_rest_api.api_gateway_rest_api.body))
    resource_change = "${md5(file("${path.module}/api_gateway.tf"))}"
  }

  lifecycle {
    create_before_destroy = true
  }

  depends_on = [
    aws_api_gateway_rest_api.api_gateway_rest_api
  ]
}

resource "aws_api_gateway_stage" "api_gateway_stage" {
  deployment_id        = aws_api_gateway_deployment.api_gateway_deployment.id
  rest_api_id          = aws_api_gateway_rest_api.api_gateway_rest_api.id
  stage_name           = "production"
  xray_tracing_enabled = true

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

resource "aws_api_gateway_gateway_response" "api_access_denied" {
  rest_api_id   = aws_api_gateway_rest_api.api_gateway_rest_api.id
  response_type = "ACCESS_DENIED"
  response_templates = {
    "application/json" = jsonencode({
      resourceType : "OperationOutcome",
      issue : [{
        severity : "error",
        code : "processing",
        diagnostics : "$context.authorizer.error"
      }]
    })
  }
  response_parameters = {
    "gatewayresponse.header.Access-Control-Allow-Origin" = "'*'"
  }
}

resource "aws_api_gateway_gateway_response" "api_default_4xx" {
  rest_api_id   = aws_api_gateway_rest_api.api_gateway_rest_api.id
  response_type = "DEFAULT_4XX"
  response_templates = {
    "application/json" = jsonencode({
      resourceType : "OperationOutcome",
      issue : [{
        severity : "error",
        code : "processing"
        diagnostics : "$context.error.message"
      }]
  }) }
  response_parameters = { "gatewayresponse.header.Access-Control-Allow-Origin" = "'*'"
  }
}

resource "aws_api_gateway_gateway_response" "api_default_5xx" {
  rest_api_id   = aws_api_gateway_rest_api.api_gateway_rest_api.id
  response_type = "DEFAULT_5XX"
  response_templates = {
    "application/json" = jsonencode({
      resourceType : "OperationOutcome",
      issue : [{
        severity : "error",
        code : "exception"
      }]
  }) }
  response_parameters = { "gatewayresponse.header.Access-Control-Allow-Origin" = "'*'"
  }
}

resource "aws_api_gateway_resource" "capability" {
  rest_api_id = aws_api_gateway_rest_api.api_gateway_rest_api.id
  parent_id   = aws_api_gateway_rest_api.api_gateway_rest_api.root_resource_id
  path_part   = "metadata"
}

resource "aws_api_gateway_method" "capability" {
  rest_api_id   = aws_api_gateway_rest_api.api_gateway_rest_api.id
  resource_id   = aws_api_gateway_resource.capability.id
  http_method   = "GET"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "capability" {
  rest_api_id = aws_api_gateway_rest_api.api_gateway_rest_api.id
  resource_id = aws_api_gateway_resource.capability.id
  http_method = aws_api_gateway_method.capability.http_method
  type        = "MOCK"
  request_templates = {
    "application/json" = jsonencode({ "statusCode" = 200 })
  }
}


resource "aws_api_gateway_method_response" "capability_200" {
  rest_api_id = aws_api_gateway_rest_api.api_gateway_rest_api.id
  resource_id = aws_api_gateway_resource.capability.id
  http_method = aws_api_gateway_method.capability.http_method
  status_code = "200"
}

resource "aws_api_gateway_integration_response" "capability" {
  rest_api_id = aws_api_gateway_rest_api.api_gateway_rest_api.id
  resource_id = aws_api_gateway_resource.capability.id
  http_method = aws_api_gateway_method.capability.http_method
  status_code = aws_api_gateway_method_response.capability_200.status_code

  response_templates = {
    "application/json" = var.capability_statement_content
  }
}
