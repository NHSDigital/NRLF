module "consumer__readDocumentReference" {
  source                 = "./modules/lambda"
  apitype                = "consumer"
  name                   = "readDocumentReference"
  region                 = local.region
  prefix                 = local.prefix
  layers                 = [module.lambda-utils.layer_arn, module.nrlf.layer_arn, module.third_party.layer_arn]
  api_gateway_source_arn = "arn:aws:execute-api:${local.region}:${var.assume_account}:${module.consumer__gateway.api_gateway_id}/*/GET/DocumentReference/{id}"
  kms_key_id             = module.kms__cloudwatch.kms_arn
}

module "consumer__searchDocumentReference" {
  source                 = "./modules/lambda"
  apitype                = "consumer"
  name                   = "searchDocumentReference"
  region                 = local.region
  prefix                 = local.prefix
  layers                 = [module.lambda-utils.layer_arn, module.nrlf.layer_arn, module.third_party.layer_arn]
  api_gateway_source_arn = "arn:aws:execute-api:${local.region}:${var.assume_account}:${module.consumer__gateway.api_gateway_id}/*/GET/DocumentReference"
  kms_key_id             = module.kms__cloudwatch.kms_arn
}

module "consumer__searchViaPostDocumentReference" {
  source                 = "./modules/lambda"
  apitype                = "consumer"
  name                   = "searchViaPostDocumentReference"
  region                 = local.region
  prefix                 = local.prefix
  layers                 = [module.lambda-utils.layer_arn, module.nrlf.layer_arn, module.third_party.layer_arn]
  api_gateway_source_arn = "arn:aws:execute-api:${local.region}:${var.assume_account}:${module.consumer__gateway.api_gateway_id}/*/POST/DocumentReference/_search"
  kms_key_id             = module.kms__cloudwatch.kms_arn
}

module "producer__createDocumentReference" {
  source                 = "./modules/lambda"
  apitype                = "producer"
  name                   = "createDocumentReference"
  region                 = local.region
  prefix                 = local.prefix
  layers                 = [module.lambda-utils.layer_arn, module.nrlf.layer_arn, module.third_party.layer_arn]
  api_gateway_source_arn = "arn:aws:execute-api:${local.region}:${var.assume_account}:${module.producer__gateway.api_gateway_id}/*/POST/DocumentReference"
  kms_key_id             = module.kms__cloudwatch.kms_arn
}

module "producer__deleteDocumentReference" {
  source                 = "./modules/lambda"
  apitype                = "producer"
  name                   = "deleteDocumentReference"
  region                 = local.region
  prefix                 = local.prefix
  layers                 = [module.lambda-utils.layer_arn, module.nrlf.layer_arn, module.third_party.layer_arn]
  api_gateway_source_arn = "arn:aws:execute-api:${local.region}:${var.assume_account}:${module.producer__gateway.api_gateway_id}/*/DELETE/DocumentReference/{id}"
  kms_key_id             = module.kms__cloudwatch.kms_arn
}

module "producer__readDocumentReference" {
  source                 = "./modules/lambda"
  apitype                = "producer"
  name                   = "readDocumentReference"
  region                 = local.region
  prefix                 = local.prefix
  layers                 = [module.lambda-utils.layer_arn, module.nrlf.layer_arn, module.third_party.layer_arn]
  api_gateway_source_arn = "arn:aws:execute-api:${local.region}:${var.assume_account}:${module.producer__gateway.api_gateway_id}/*/GET/DocumentReference/{id}"
  kms_key_id             = module.kms__cloudwatch.kms_arn
}


module "producer__searchDocumentReference" {
  source                 = "./modules/lambda"
  apitype                = "producer"
  name                   = "searchDocumentReference"
  region                 = local.region
  prefix                 = local.prefix
  layers                 = [module.lambda-utils.layer_arn, module.nrlf.layer_arn, module.third_party.layer_arn]
  api_gateway_source_arn = "arn:aws:execute-api:${local.region}:${var.assume_account}:${module.producer__gateway.api_gateway_id}/*/GET/DocumentReference"
  kms_key_id             = module.kms__cloudwatch.kms_arn
}

module "producer__updateDocumentReference" {
  source                 = "./modules/lambda"
  apitype                = "producer"
  name                   = "updateDocumentReference"
  region                 = local.region
  prefix                 = local.prefix
  layers                 = [module.lambda-utils.layer_arn, module.nrlf.layer_arn, module.third_party.layer_arn]
  api_gateway_source_arn = "arn:aws:execute-api:${local.region}:${var.assume_account}:${module.producer__gateway.api_gateway_id}/*/PUT/DocumentReference/{id}"
  kms_key_id             = module.kms__cloudwatch.kms_arn
}
