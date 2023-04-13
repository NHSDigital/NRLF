resource "aws_iam_role" "lambda_role" {
  name = substr("${var.prefix}--${replace(var.parent_path, "/", "--")}--${var.name}", 0, 64)
  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Principal = {
          Service = "lambda.amazonaws.com"
        },
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_policy_attachment" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"

  depends_on = [
    aws_iam_role.lambda_role
  ]
}

resource "aws_iam_role_policy_attachment" "additional_policies" {
  role       = aws_iam_role.lambda_role.name
  count      = length(var.additional_policies)
  policy_arn = var.additional_policies[count.index]
}
