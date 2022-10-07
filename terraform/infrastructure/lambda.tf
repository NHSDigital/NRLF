module "consumer__readDocumentReference" {
  source                 = "./modules/lambda"
  apitype                = "consumer"
  name                   = "readDocumentReference"
  region                 = local.region
  assume_account         = var.assume_account
  prefix                 = local.prefix
  layers                 = [module.lambda-utils.layer_arn, module.nrlf.layer_arn, module.third_party.layer_arn]
  api_gateway_source_arn = "arn:aws:execute-api:${local.region}:${var.assume_account}:${aws_api_gateway_rest_api.consumer.id}/*/DocumentReference/{id}"
}

module "consumer__searchDocumentReference" {
  source                 = "./modules/lambda"
  apitype                = "consumer"
  name                   = "searchDocumentReference"
  region                 = local.region
  assume_account         = var.assume_account
  prefix                 = local.prefix
  layers                 = [module.lambda-utils.layer_arn, module.nrlf.layer_arn, module.third_party.layer_arn]
  api_gateway_source_arn = "arn:aws:execute-api:${local.region}:${var.assume_account}:${aws_api_gateway_rest_api.consumer.id}/*/DocumentReference"
}

module "consumer__searchViaPostDocumentReference" {
  source                 = "./modules/lambda"
  apitype                = "consumer"
  name                   = "searchViaPostDocumentReference"
  region                 = local.region
  assume_account         = var.assume_account
  prefix                 = local.prefix
  layers                 = [module.lambda-utils.layer_arn, module.nrlf.layer_arn, module.third_party.layer_arn]
  api_gateway_source_arn = "arn:aws:execute-api:${local.region}:${var.assume_account}:${aws_api_gateway_rest_api.consumer.id}/*/DocumentReference/_search"
}

module "producer__createDocumentReference" {
  source                 = "./modules/lambda"
  apitype                = "producer"
  name                   = "createDocumentReference"
  region                 = local.region
  assume_account         = var.assume_account
  prefix                 = local.prefix
  layers                 = [module.lambda-utils.layer_arn, module.nrlf.layer_arn, module.third_party.layer_arn]
  api_gateway_source_arn = "arn:aws:execute-api:${local.region}:${var.assume_account}:${aws_api_gateway_rest_api.producer.id}/*/DocumentReference"
}

module "producer__deleteDocumentReference" {
  source                 = "./modules/lambda"
  apitype                = "producer"
  name                   = "deleteDocumentReference"
  region                 = local.region
  assume_account         = var.assume_account
  prefix                 = local.prefix
  layers                 = [module.lambda-utils.layer_arn, module.nrlf.layer_arn, module.third_party.layer_arn]
  api_gateway_source_arn = "arn:aws:execute-api:${local.region}:${var.assume_account}:${aws_api_gateway_rest_api.producer.id}/*/DocumentReference/{id}"
}

module "producer__readDocumentReference" {
  source                 = "./modules/lambda"
  apitype                = "producer"
  name                   = "readDocumentReference"
  region                 = local.region
  assume_account         = var.assume_account
  prefix                 = local.prefix
  layers                 = [module.lambda-utils.layer_arn, module.nrlf.layer_arn, module.third_party.layer_arn]
  api_gateway_source_arn = "arn:aws:execute-api:${local.region}:${var.assume_account}:${aws_api_gateway_rest_api.producer.id}/*/DocumentReference/{id}"
}


module "producer__searchDocumentReference" {
  source                 = "./modules/lambda"
  apitype                = "producer"
  name                   = "searchDocumentReference"
  region                 = local.region
  assume_account         = var.assume_account
  prefix                 = local.prefix
  layers                 = [module.lambda-utils.layer_arn, module.nrlf.layer_arn, module.third_party.layer_arn]
  api_gateway_source_arn = "arn:aws:execute-api:${local.region}:${var.assume_account}:${aws_api_gateway_rest_api.producer.id}/*/DocumentReference"
}

module "producer__updateDocumentReference" {
  source                 = "./modules/lambda"
  apitype                = "producer"
  name                   = "updateDocumentReference"
  region                 = local.region
  assume_account         = var.assume_account
  prefix                 = local.prefix
  layers                 = [module.lambda-utils.layer_arn, module.nrlf.layer_arn, module.third_party.layer_arn]
  api_gateway_source_arn = "arn:aws:execute-api:${local.region}:${var.assume_account}:${aws_api_gateway_rest_api.producer.id}/*/DocumentReference/{id}"
}