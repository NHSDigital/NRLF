module "kms__cloudwatch" {
  source         = "./modules/kms"
  name           = "cloudwatch"
  assume_account = local.aws_account_id
  prefix         = local.prefix
}

data "aws_kms_key" "document-pointer-kms" {
  key_id = "alias/${local.prefix}--document-pointer"
  depends_on = [
    aws_dynamodb_table.document-pointer
  ]
}
