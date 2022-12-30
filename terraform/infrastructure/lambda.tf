module "consumer__readDocumentReference" {
  source                 = "./modules/lambda"
  apitype                = "consumer"
  name                   = "readDocumentReference"
  region                 = local.region
  prefix                 = local.prefix
  layers                 = [module.lambda-utils.layer_arn, module.nrlf.layer_arn, module.third_party.layer_arn]
  api_gateway_source_arn = ["arn:aws:execute-api:${local.region}:${var.assume_account}:${module.consumer__gateway.api_gateway_id}/*/GET/DocumentReference/{id}"]
  kms_key_id             = module.kms__cloudwatch.kms_arn
  environment_variables = {
    DOCUMENT_POINTER_TABLE_NAME = aws_dynamodb_table.document-pointer.name
    PREFIX                      = "${local.prefix}--"
    ENVIRONMENT                 = local.environment
  }
  additional_policies = [
    aws_iam_policy.document-pointer__dynamodb-read.arn,
    aws_iam_policy.document-pointer__kms-read-write.arn
  ]
  handler = "api.consumer.readDocumentReference.index.handler"
}

module "consumer__searchDocumentReference" {
  source                 = "./modules/lambda"
  apitype                = "consumer"
  name                   = "searchDocumentReference"
  region                 = local.region
  prefix                 = local.prefix
  layers                 = [module.lambda-utils.layer_arn, module.nrlf.layer_arn, module.third_party.layer_arn]
  api_gateway_source_arn = ["arn:aws:execute-api:${local.region}:${var.assume_account}:${module.consumer__gateway.api_gateway_id}/*/GET/DocumentReference"]
  kms_key_id             = module.kms__cloudwatch.kms_arn
  environment_variables = {
    DOCUMENT_POINTER_TABLE_NAME = aws_dynamodb_table.document-pointer.name
    PREFIX                      = "${local.prefix}--"
    ENVIRONMENT                 = local.environment
  }
  additional_policies = [
    aws_iam_policy.document-pointer__dynamodb-read.arn,
    aws_iam_policy.document-pointer__kms-read-write.arn
  ]
  handler = "api.consumer.searchDocumentReference.index.handler"
}

module "consumer__searchPostDocumentReference" {
  source                 = "./modules/lambda"
  apitype                = "consumer"
  name                   = "searchPostDocumentReference"
  region                 = local.region
  prefix                 = local.prefix
  layers                 = [module.lambda-utils.layer_arn, module.nrlf.layer_arn, module.third_party.layer_arn]
  api_gateway_source_arn = ["arn:aws:execute-api:${local.region}:${var.assume_account}:${module.consumer__gateway.api_gateway_id}/*/POST/DocumentReference/_search"]
  kms_key_id             = module.kms__cloudwatch.kms_arn
  environment_variables = {
    DOCUMENT_POINTER_TABLE_NAME = aws_dynamodb_table.document-pointer.name
    PREFIX                      = "${local.prefix}--"
    ENVIRONMENT                 = local.environment
  }
  additional_policies = [
    aws_iam_policy.document-pointer__dynamodb-read.arn,
    aws_iam_policy.document-pointer__kms-read-write.arn
  ]
  handler = "api.consumer.searchPostDocumentReference.index.handler"
}

module "producer__createDocumentReference" {
  source                 = "./modules/lambda"
  apitype                = "producer"
  name                   = "createDocumentReference"
  region                 = local.region
  prefix                 = local.prefix
  layers                 = [module.lambda-utils.layer_arn, module.nrlf.layer_arn, module.third_party.layer_arn]
  api_gateway_source_arn = ["arn:aws:execute-api:${local.region}:${var.assume_account}:${module.producer__gateway.api_gateway_id}/*/POST/DocumentReference"]
  kms_key_id             = module.kms__cloudwatch.kms_arn
  environment_variables = {
    DOCUMENT_POINTER_TABLE_NAME = aws_dynamodb_table.document-pointer.name
    PREFIX                      = "${local.prefix}--"
    ENVIRONMENT                 = local.environment
  }
  additional_policies = [
    aws_iam_policy.document-pointer__dynamodb-write.arn,
    aws_iam_policy.document-pointer__kms-read-write.arn
  ]
  handler = "api.producer.createDocumentReference.index.handler"
}

module "producer__deleteDocumentReference" {
  source                 = "./modules/lambda"
  apitype                = "producer"
  name                   = "deleteDocumentReference"
  region                 = local.region
  prefix                 = local.prefix
  layers                 = [module.lambda-utils.layer_arn, module.nrlf.layer_arn, module.third_party.layer_arn]
  api_gateway_source_arn = ["arn:aws:execute-api:${local.region}:${var.assume_account}:${module.producer__gateway.api_gateway_id}/*/DELETE/DocumentReference/{id}"]
  kms_key_id             = module.kms__cloudwatch.kms_arn
  environment_variables = {
    DOCUMENT_POINTER_TABLE_NAME = aws_dynamodb_table.document-pointer.name
    PREFIX                      = "${local.prefix}--"
    ENVIRONMENT                 = local.environment
  }
  additional_policies = [
    aws_iam_policy.document-pointer__dynamodb-write.arn,
    aws_iam_policy.document-pointer__dynamodb-read.arn,
    aws_iam_policy.document-pointer__kms-read-write.arn
  ]
  handler = "api.producer.deleteDocumentReference.index.handler"
}

module "producer__readDocumentReference" {
  source                 = "./modules/lambda"
  apitype                = "producer"
  name                   = "readDocumentReference"
  region                 = local.region
  prefix                 = local.prefix
  layers                 = [module.lambda-utils.layer_arn, module.nrlf.layer_arn, module.third_party.layer_arn]
  api_gateway_source_arn = ["arn:aws:execute-api:${local.region}:${var.assume_account}:${module.producer__gateway.api_gateway_id}/*/GET/DocumentReference/{id}"]
  kms_key_id             = module.kms__cloudwatch.kms_arn
  environment_variables = {
    DOCUMENT_POINTER_TABLE_NAME = aws_dynamodb_table.document-pointer.name
    PREFIX                      = "${local.prefix}--"
    ENVIRONMENT                 = local.environment
  }
  additional_policies = [
    aws_iam_policy.document-pointer__dynamodb-read.arn,
    aws_iam_policy.document-pointer__kms-read-write.arn
  ]
  handler = "api.producer.readDocumentReference.index.handler"
}


module "producer__searchDocumentReference" {
  source                 = "./modules/lambda"
  apitype                = "producer"
  name                   = "searchDocumentReference"
  region                 = local.region
  prefix                 = local.prefix
  layers                 = [module.lambda-utils.layer_arn, module.nrlf.layer_arn, module.third_party.layer_arn]
  api_gateway_source_arn = ["arn:aws:execute-api:${local.region}:${var.assume_account}:${module.producer__gateway.api_gateway_id}/*/GET/DocumentReference"]
  kms_key_id             = module.kms__cloudwatch.kms_arn
  environment_variables = {
    DOCUMENT_POINTER_TABLE_NAME = aws_dynamodb_table.document-pointer.name
    PREFIX                      = "${local.prefix}--"
    ENVIRONMENT                 = local.environment
  }
  additional_policies = [
    aws_iam_policy.document-pointer__dynamodb-read.arn,
    aws_iam_policy.document-pointer__kms-read-write.arn
  ]
  handler = "api.producer.searchDocumentReference.index.handler"
}

module "producer__updateDocumentReference" {
  source                 = "./modules/lambda"
  apitype                = "producer"
  name                   = "updateDocumentReference"
  region                 = local.region
  prefix                 = local.prefix
  layers                 = [module.lambda-utils.layer_arn, module.nrlf.layer_arn, module.third_party.layer_arn]
  api_gateway_source_arn = ["arn:aws:execute-api:${local.region}:${var.assume_account}:${module.producer__gateway.api_gateway_id}/*/PUT/DocumentReference/{id}"]
  kms_key_id             = module.kms__cloudwatch.kms_arn
  environment_variables = {
    DOCUMENT_POINTER_TABLE_NAME = aws_dynamodb_table.document-pointer.name
    PREFIX                      = "${local.prefix}--"
    ENVIRONMENT                 = local.environment
  }
  additional_policies = [
    aws_iam_policy.document-pointer__dynamodb-read.arn,
    aws_iam_policy.document-pointer__dynamodb-write.arn,
    aws_iam_policy.document-pointer__kms-read-write.arn
  ]
  handler = "api.producer.updateDocumentReference.index.handler"

  depends_on = [
    aws_iam_policy.document-pointer__dynamodb-read,
    aws_iam_policy.document-pointer__dynamodb-write,
    aws_iam_policy.document-pointer__kms-read-write
  ]
}

module "producer__authoriser_lambda" {
  source     = "./modules/lambda"
  apitype    = "producer"
  name       = "authoriser"
  region     = local.region
  prefix     = local.prefix
  layers     = [module.lambda-utils.layer_arn, module.nrlf.layer_arn, module.third_party.layer_arn]
  kms_key_id = module.kms__cloudwatch.kms_arn
  environment_variables = {
    PREFIX      = "${local.prefix}--"
    ENVIRONMENT = local.environment
  }
  additional_policies = [
    aws_iam_policy.auth_producer__dynamodb-read.arn,
    aws_iam_policy.auth_producer__kms-read-write.arn
  ]
  handler = "api.producer.authoriser.index.handler"
  depends_on = [
    aws_iam_policy.auth_producer__dynamodb-read,
    aws_iam_policy.auth_producer__kms-read-write
  ]
}

module "consumer__authoriser_lambda" {
  source     = "./modules/lambda"
  apitype    = "consumer"
  name       = "authoriser"
  region     = local.region
  prefix     = local.prefix
  layers     = [module.lambda-utils.layer_arn, module.nrlf.layer_arn, module.third_party.layer_arn]
  kms_key_id = module.kms__cloudwatch.kms_arn
  environment_variables = {
    PREFIX      = "${local.prefix}--"
    ENVIRONMENT = local.environment
  }
  additional_policies = [
    aws_iam_policy.auth_consumer__dynamodb-read.arn,
    aws_iam_policy.auth_consumer__kms-read-write.arn
  ]
  handler = "api.consumer.authoriser.index.handler"
  depends_on = [
    aws_iam_policy.auth_consumer__dynamodb-read,
    aws_iam_policy.auth_consumer__kms-read-write
  ]
}

module "consumer__status" {
  source                 = "./modules/lambda"
  apitype                = "consumer"
  name                   = "status"
  region                 = local.region
  prefix                 = local.prefix
  layers                 = [module.lambda-utils.layer_arn, module.nrlf.layer_arn, module.third_party.layer_arn]
  api_gateway_source_arn = ["arn:aws:execute-api:${local.region}:${var.assume_account}:${module.consumer__gateway.api_gateway_id}/*/GET/_status"]
  kms_key_id             = module.kms__cloudwatch.kms_arn
  environment_variables = {
    DOCUMENT_POINTER_TABLE_NAME = aws_dynamodb_table.document-pointer.name
    PREFIX                      = "${local.prefix}--"
    ENVIRONMENT                 = local.environment
  }
  additional_policies = [
    aws_iam_policy.document-pointer__dynamodb-read.arn,
    aws_iam_policy.document-pointer__kms-read-write.arn
  ]
  handler = "api.consumer.status.index.handler"
}


module "producer__status" {
  source                 = "./modules/lambda"
  apitype                = "producer"
  name                   = "status"
  region                 = local.region
  prefix                 = local.prefix
  layers                 = [module.lambda-utils.layer_arn, module.nrlf.layer_arn, module.third_party.layer_arn]
  api_gateway_source_arn = ["arn:aws:execute-api:${local.region}:${var.assume_account}:${module.producer__gateway.api_gateway_id}/*/GET/_status"]
  kms_key_id             = module.kms__cloudwatch.kms_arn
  environment_variables = {
    DOCUMENT_POINTER_TABLE_NAME = aws_dynamodb_table.document-pointer.name
    PREFIX                      = "${local.prefix}--"
    ENVIRONMENT                 = local.environment
  }
  additional_policies = [
    aws_iam_policy.document-pointer__dynamodb-read.arn,
    aws_iam_policy.document-pointer__kms-read-write.arn
  ]
  handler = "api.producer.status.index.handler"
}
