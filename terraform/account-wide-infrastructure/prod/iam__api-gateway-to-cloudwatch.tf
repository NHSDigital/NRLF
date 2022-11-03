resource "aws_iam_role" "api_gateway_to_cloudwatch" {
  name = "${local.prefix}--api-gateway-cloudwatch-logs"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          "Service" : "apigateway.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "api_gateway_to_cloudwatch" {
  role       = aws_iam_role.api_gateway_to_cloudwatch.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonAPIGatewayPushToCloudWatchLogs"

  depends_on = [
    aws_iam_role.api_gateway_to_cloudwatch
  ]
}

resource "aws_api_gateway_account" "api_gateway_account" {
  cloudwatch_role_arn = aws_iam_role.api_gateway_to_cloudwatch.arn

  depends_on = [
    aws_iam_role.api_gateway_to_cloudwatch
  ]
}
