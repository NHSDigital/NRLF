resource "aws_iam_role" "lambda_role" {
  name               = substr("${var.prefix}--api--${var.apitype}--${var.name}", 0, 64)
  assume_role_policy = jsonencode({
    Version   = "2012-10-17",
    Statement = [
      {
        Effect    = "Allow",
        Principal = {
          Service = "lambda.amazonaws.com"
        },
        Action = "sts:AssumeRole"
      }
    ]
  })
  managed_policy_arns = concat(var.policy_arns, ["arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"])
}

# resource "aws_iam_role_policy_attachment" "lambda_policy_attachment" {
#   role       = aws_iam_role.lambda_role.name
#   policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"

  depends_on = [
    aws_iam_role.lambda_role
  ]
}

resource "aws_iam_role_policy_attachment" "additional_policies" {
  for_each   = toset(var.additional_policies)
  role       = aws_iam_role.lambda_role.name
  policy_arn = each.key

  depends_on = [
    aws_iam_role.lambda_role
  ]
}
