module "mi" {
  source             = "./modules/postgres_cluster"
  schema_path        = "../../mi/schema/schema.sql"
  name               = "mi"
  prefix             = local.prefix
  environment        = local.environment
  region             = local.region
  cloudwatch_kms_arn = module.kms__cloudwatch.kms_arn
  account_name       = local.account_name
  layers             = [module.third_party.layer_arn]
  assume_account     = var.assume_account
}