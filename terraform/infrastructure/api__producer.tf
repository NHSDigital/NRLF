resource "aws_api_gateway_rest_api" "producer" {
  name        = "${local.prefix}--producer"
  description = "Terraform Serverless Application Example"
  body = templatefile("${path.module}/../../api/producer/swagger.yaml", {
    environment                    = local.environment
    method_searchDocumentReference = "arn:aws:apigateway:eu-west-2:lambda:path/2015-03-31/functions/arn:aws:lambda:eu-west-2:${var.assume_account}:function:${local.prefix}--api--producer--searchDocumentReference/invocations"
    method_readDocumentReference   = "arn:aws:apigateway:eu-west-2:lambda:path/2015-03-31/functions/arn:aws:lambda:eu-west-2:${var.assume_account}:function:${local.prefix}--api--producer--readDocumentReference/invocations"
    method_createDocumentReference = "arn:aws:apigateway:eu-west-2:lambda:path/2015-03-31/functions/arn:aws:lambda:eu-west-2:${var.assume_account}:function:${local.prefix}--api--producer--createDocumentReference/invocations"
    method_updateDocumentReference = "arn:aws:apigateway:eu-west-2:lambda:path/2015-03-31/functions/arn:aws:lambda:eu-west-2:${var.assume_account}:function:${local.prefix}--api--producer--updateDocumentReference/invocations"
    method_deleteDocumentReference = "arn:aws:apigateway:eu-west-2:lambda:path/2015-03-31/functions/arn:aws:lambda:eu-west-2:${var.assume_account}:function:${local.prefix}--api--producer--deleteDocumentReference/invocations"
  })
}

resource "aws_api_gateway_deployment" "producer" {
  rest_api_id = aws_api_gateway_rest_api.producer.id

  triggers = {
    redeployment = sha1(jsonencode(aws_api_gateway_rest_api.producer.body))
  }

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_api_gateway_stage" "producer" {
  deployment_id = aws_api_gateway_deployment.producer.id
  rest_api_id   = aws_api_gateway_rest_api.producer.id
  stage_name    = "production"

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.producer__access_logs.arn
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
    aws_cloudwatch_log_group.producer__access_logs,
    aws_cloudwatch_log_group.producer__execution_logs
  ]
}

resource "aws_api_gateway_method_settings" "producer" {
  rest_api_id = aws_api_gateway_rest_api.producer.id
  stage_name  = aws_api_gateway_stage.producer.stage_name
  method_path = "*/*"
  settings {
    logging_level      = "ERROR"
    data_trace_enabled = true
  }
}

resource "aws_cloudwatch_log_group" "producer__access_logs" {
  name = "/aws/api-gateway/access-logs/${aws_api_gateway_rest_api.producer.name}"

  kms_key_id = aws_kms_key.cloudwatch.arn

}

resource "aws_cloudwatch_log_group" "producer__execution_logs" {
  name = "API-Gateway-Execution-Logs_${aws_api_gateway_rest_api.producer.id}/production"

  kms_key_id = aws_kms_key.cloudwatch.arn

}
