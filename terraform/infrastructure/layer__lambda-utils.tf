resource "aws_lambda_layer_version" "lambda-utils" {
  layer_name          = "${local.prefix}--lambda-utils"
  filename            = "${path.module}/../../layer/lambda_utils/dist/lambda_utils.zip"
  source_code_hash    = filebase64sha256("${path.module}/../../layer/lambda_utils/dist/lambda_utils.zip")
  compatible_runtimes = ["python3.9"]
}
