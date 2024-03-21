resource "aws_lambda_layer_version" "lambda_layer" {
  layer_name          = "${var.prefix}--${replace(var.name, "_", "-")}"
  filename            = "${path.module}/../../../../layer/${var.name}/dist/${var.name}.zip"
  source_code_hash    = filebase64sha256("${path.module}/../../../../layer/${var.name}/dist/${var.name}.zip")
  compatible_runtimes = ["python3.12"]
}
