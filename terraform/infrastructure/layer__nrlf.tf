resource "aws_lambda_layer_version" "nrlf" {
  layer_name          = "${local.prefix}--nrlf"
  filename            = "${path.module}/../../layer/nrlf/dist/nrlf.zip"
  source_code_hash    = filebase64sha256("${path.module}/../../layer/nrlf/dist/nrlf.zip")
  compatible_runtimes = ["python3.9"]
}
