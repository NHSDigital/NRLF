resource "aws_iam_role" "api_authorizer" {
  name = "${var.prefix}-${var.apitype}-api-authorizer"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action = "sts:AssumeRole",
        Principal = {
          Service = "apigateway.amazonaws.com"
        },
        Effect = "Allow",
        Sid    = ""
      }
    ]
  })
}
