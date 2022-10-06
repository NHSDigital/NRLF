resource "aws_api_gateway_rest_api" "consumer" {
  name        = "${local.prefix}--consumer"
  description = "Terraform Serverless Application Example"
  body = templatefile("${path.module}/../../api/consumer/swagger.yaml", {
    environment                           = local.environment
    method_searchDocumentReference        = "arn:aws:apigateway:eu-west-2:lambda:path/2015-03-31/functions/arn:aws:lambda:eu-west-2:${var.assume_account}:function:${local.prefix}--api--consumer--searchDocumentReference/invocations"
    method_searchViaPostDocumentReference = "arn:aws:apigateway:eu-west-2:lambda:path/2015-03-31/functions/arn:aws:lambda:eu-west-2:${var.assume_account}:function:${local.prefix}--api--consumer--searchViaPostDocumentReference/invocations"
    method_readDocumentReference          = "arn:aws:apigateway:eu-west-2:lambda:path/2015-03-31/functions/arn:aws:lambda:eu-west-2:${var.assume_account}:function:${local.prefix}--api--consumer--readDocumentReference/invocations"
  })
}

resource "aws_api_gateway_deployment" "consumer" {
  rest_api_id = aws_api_gateway_rest_api.consumer.id

  triggers = {
    redeployment = sha1(jsonencode(aws_api_gateway_rest_api.consumer.body))
  }

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_api_gateway_stage" "consumer" {
  deployment_id = aws_api_gateway_deployment.consumer.id
  rest_api_id   = aws_api_gateway_rest_api.consumer.id
  stage_name    = "production"

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.consumer__access_logs.arn
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
      environment : local.environment
    })
  }

  depends_on = [
    aws_cloudwatch_log_group.consumer__access_logs,
    aws_cloudwatch_log_group.consumer__execution_logs
  ]
}

resource "aws_api_gateway_method_settings" "consumer" {
  rest_api_id = aws_api_gateway_rest_api.consumer.id
  stage_name  = aws_api_gateway_stage.consumer.stage_name
  method_path = "*/*"
  settings {
    logging_level      = "ERROR"
    data_trace_enabled = true
  }
}

resource "aws_cloudwatch_log_group" "consumer__access_logs" {
  name = "/aws/api-gateway/access-logs/${aws_api_gateway_rest_api.consumer.name}"

  kms_key_id = aws_kms_key.cloudwatch.arn

}

resource "aws_cloudwatch_log_group" "consumer__execution_logs" {
  name = "API-Gateway-Execution-Logs_${aws_api_gateway_rest_api.consumer.id}/production"

  kms_key_id = aws_kms_key.cloudwatch.arn

}
