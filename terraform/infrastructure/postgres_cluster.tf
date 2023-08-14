module "mi" {
  source                     = "./modules/postgres_cluster"
  schema_path                = "../../mi/schema/schema.sql"
  static_dimensions_path     = "../../mi/schema/static_dimensions.sql"
  name                       = "mi"
  prefix                     = local.prefix
  environment                = local.environment
  region                     = local.region
  cloudwatch_kms_arn         = module.kms__cloudwatch.kms_arn
  account_name               = local.account_name
  layers                     = [module.third_party.layer_arn]
  assume_account             = var.assume_account
  dynamodb_table             = aws_dynamodb_table.document-pointer
  dynamodb_table_kms_key_arn = data.aws_kms_key.document-pointer-kms.arn
}
