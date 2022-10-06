resource "aws_lambda_layer_version" "third-party" {
  layer_name          = "${local.prefix}--third_party"
  filename            = "${path.module}/../../layer/third_party/dist/third_party.zip"
  source_code_hash    = filebase64sha256("${path.module}/../../layer/third_party/dist/third_party.zip")
  compatible_runtimes = ["python3.9"]
}
