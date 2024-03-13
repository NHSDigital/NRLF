module "consumer__readDocumentReference" {
  source                 = "./modules/lambda"
  parent_path            = "api/consumer"
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
    SPLUNK_INDEX                = module.firehose__processor.splunk.index
  }
  additional_policies = [
    aws_iam_policy.document-pointer__dynamodb-read.arn,
    aws_iam_policy.document-pointer__kms-read-write.arn
  ]
  firehose_subscriptions = [
    module.firehose__processor.firehose_subscription
  ]
  handler = "api.consumer.readDocumentReference.index.handler"
}

module "consumer__countDocumentReference" {
  source                 = "./modules/lambda"
  parent_path            = "api/consumer"
  name                   = "countDocumentReference"
  region                 = local.region
  prefix                 = local.prefix
  layers                 = [module.lambda-utils.layer_arn, module.nrlf.layer_arn, module.third_party.layer_arn]
  api_gateway_source_arn = ["arn:aws:execute-api:${local.region}:${var.assume_account}:${module.consumer__gateway.api_gateway_id}/*/GET/DocumentReference/_count"]
  kms_key_id             = module.kms__cloudwatch.kms_arn
  environment_variables = {
    DOCUMENT_POINTER_TABLE_NAME = aws_dynamodb_table.document-pointer.name
    PREFIX                      = "${local.prefix}--"
    ENVIRONMENT                 = local.environment
    SPLUNK_INDEX                = module.firehose__processor.splunk.index
  }
  additional_policies = [
    aws_iam_policy.document-pointer__dynamodb-read.arn,
    aws_iam_policy.document-pointer__kms-read-write.arn
  ]
  firehose_subscriptions = [
    module.firehose__processor.firehose_subscription
  ]
  handler = "api.consumer.countDocumentReference.index.handler"
}

module "consumer__searchDocumentReference" {
  source                 = "./modules/lambda"
  parent_path            = "api/consumer"
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
    SPLUNK_INDEX                = module.firehose__processor.splunk.index
  }
  additional_policies = [
    aws_iam_policy.document-pointer__dynamodb-read.arn,
    aws_iam_policy.document-pointer__kms-read-write.arn
  ]
  firehose_subscriptions = [
    module.firehose__processor.firehose_subscription
  ]
  handler = "api.consumer.searchDocumentReference.index.handler"
}

module "consumer__searchPostDocumentReference" {
  source                 = "./modules/lambda"
  parent_path            = "api/consumer"
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
    SPLUNK_INDEX                = module.firehose__processor.splunk.index
  }
  additional_policies = [
    aws_iam_policy.document-pointer__dynamodb-read.arn,
    aws_iam_policy.document-pointer__kms-read-write.arn
  ]
  firehose_subscriptions = [
    module.firehose__processor.firehose_subscription
  ]
  handler = "api.consumer.searchPostDocumentReference.index.handler"
}

module "producer__createDocumentReference" {
  source                 = "./modules/lambda"
  parent_path            = "api/producer"
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
    SPLUNK_INDEX                = module.firehose__processor.splunk.index
  }
  additional_policies = [
    aws_iam_policy.document-pointer__dynamodb-write.arn,
    aws_iam_policy.document-pointer__dynamodb-read.arn,
    aws_iam_policy.document-pointer__kms-read-write.arn
  ]
  firehose_subscriptions = [
    module.firehose__processor.firehose_subscription
  ]
  handler = "api.producer.createDocumentReference.index.handler"
}

module "producer__deleteDocumentReference" {
  source                 = "./modules/lambda"
  parent_path            = "api/producer"
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
    SPLUNK_INDEX                = module.firehose__processor.splunk.index
  }
  additional_policies = [
    aws_iam_policy.document-pointer__dynamodb-write.arn,
    aws_iam_policy.document-pointer__dynamodb-read.arn,
    aws_iam_policy.document-pointer__kms-read-write.arn
  ]
  firehose_subscriptions = [
    module.firehose__processor.firehose_subscription
  ]
  handler = "api.producer.deleteDocumentReference.index.handler"
}

module "producer__readDocumentReference" {
  source                 = "./modules/lambda"
  parent_path            = "api/producer"
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
    SPLUNK_INDEX                = module.firehose__processor.splunk.index
  }
  additional_policies = [
    aws_iam_policy.document-pointer__dynamodb-read.arn,
    aws_iam_policy.document-pointer__kms-read-write.arn
  ]
  firehose_subscriptions = [
    module.firehose__processor.firehose_subscription
  ]
  handler = "api.producer.readDocumentReference.index.handler"
}

module "producer__searchDocumentReference" {
  source                 = "./modules/lambda"
  parent_path            = "api/producer"
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
    SPLUNK_INDEX                = module.firehose__processor.splunk.index
  }
  additional_policies = [
    aws_iam_policy.document-pointer__dynamodb-read.arn,
    aws_iam_policy.document-pointer__kms-read-write.arn
  ]
  firehose_subscriptions = [
    module.firehose__processor.firehose_subscription
  ]
  handler = "api.producer.searchDocumentReference.index.handler"
}

module "producer__searchPostDocumentReference" {
  source                 = "./modules/lambda"
  parent_path            = "api/producer"
  name                   = "searchPostDocumentReference"
  region                 = local.region
  prefix                 = local.prefix
  layers                 = [module.lambda-utils.layer_arn, module.nrlf.layer_arn, module.third_party.layer_arn]
  api_gateway_source_arn = ["arn:aws:execute-api:${local.region}:${var.assume_account}:${module.producer__gateway.api_gateway_id}/*/POST/DocumentReference/_search"]
  kms_key_id             = module.kms__cloudwatch.kms_arn
  environment_variables = {
    DOCUMENT_POINTER_TABLE_NAME = aws_dynamodb_table.document-pointer.name
    PREFIX                      = "${local.prefix}--"
    ENVIRONMENT                 = local.environment
    SPLUNK_INDEX                = module.firehose__processor.splunk.index
  }
  additional_policies = [
    aws_iam_policy.document-pointer__dynamodb-read.arn,
    aws_iam_policy.document-pointer__kms-read-write.arn
  ]
  firehose_subscriptions = [
    module.firehose__processor.firehose_subscription
  ]
  handler = "api.producer.searchPostDocumentReference.index.handler"
}

module "producer__updateDocumentReference" {
  source                 = "./modules/lambda"
  parent_path            = "api/producer"
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
    SPLUNK_INDEX                = module.firehose__processor.splunk.index
  }
  additional_policies = [
    aws_iam_policy.document-pointer__dynamodb-read.arn,
    aws_iam_policy.document-pointer__dynamodb-write.arn,
    aws_iam_policy.document-pointer__kms-read-write.arn
  ]
  firehose_subscriptions = [
    module.firehose__processor.firehose_subscription
  ]
  handler = "api.producer.updateDocumentReference.index.handler"

  depends_on = [
    aws_iam_policy.document-pointer__dynamodb-read,
    aws_iam_policy.document-pointer__dynamodb-write,
    aws_iam_policy.document-pointer__kms-read-write
  ]
}

module "producer__upsertDocumentReference" {
  source                 = "./modules/lambda"
  parent_path            = "api/producer"
  name                   = "upsertDocumentReference"
  region                 = local.region
  prefix                 = local.prefix
  layers                 = [module.lambda-utils.layer_arn, module.nrlf.layer_arn, module.third_party.layer_arn]
  api_gateway_source_arn = ["arn:aws:execute-api:${local.region}:${var.assume_account}:${module.producer__gateway.api_gateway_id}/*/PUT/DocumentReference"]
  kms_key_id             = module.kms__cloudwatch.kms_arn
  environment_variables = {
    DOCUMENT_POINTER_TABLE_NAME = aws_dynamodb_table.document-pointer.name
    PREFIX                      = "${local.prefix}--"
    ENVIRONMENT                 = local.environment
    SPLUNK_INDEX                = module.firehose__processor.splunk.index
  }
  additional_policies = [
    aws_iam_policy.document-pointer__dynamodb-write.arn,
    aws_iam_policy.document-pointer__dynamodb-read.arn,
    aws_iam_policy.document-pointer__kms-read-write.arn
  ]
  firehose_subscriptions = [
    module.firehose__processor.firehose_subscription
  ]
  handler = "api.producer.upsertDocumentReference.index.handler"
}

module "producer__authoriser_lambda" {
  source      = "./modules/lambda"
  parent_path = "api/producer"
  name        = "authoriser"
  region      = local.region
  prefix      = local.prefix
  layers      = [module.lambda-utils.layer_arn, module.nrlf.layer_arn, module.third_party.layer_arn]
  kms_key_id  = module.kms__cloudwatch.kms_arn
  environment_variables = {
    PREFIX       = "${local.prefix}--"
    ENVIRONMENT  = local.environment
    SPLUNK_INDEX = module.firehose__processor.splunk.index
    AUTH_STORE   = aws_s3_bucket.authorization-store.id
  }
  additional_policies = [
    aws_iam_policy.read-authorization-store-s3.arn,
  ]
  firehose_subscriptions = [
    module.firehose__processor.firehose_subscription
  ]
  handler = "api.producer.authoriser.index.handler"
  depends_on = [
  ]
}

module "consumer__authoriser_lambda" {
  source      = "./modules/lambda"
  parent_path = "api/consumer"
  name        = "authoriser"
  region      = local.region
  prefix      = local.prefix
  layers      = [module.lambda-utils.layer_arn, module.nrlf.layer_arn, module.third_party.layer_arn]
  kms_key_id  = module.kms__cloudwatch.kms_arn
  environment_variables = {
    PREFIX       = "${local.prefix}--"
    ENVIRONMENT  = local.environment
    SPLUNK_INDEX = module.firehose__processor.splunk.index
    AUTH_STORE   = aws_s3_bucket.authorization-store.id
  }
  additional_policies = [
    aws_iam_policy.read-authorization-store-s3.arn,
  ]
  firehose_subscriptions = [
    module.firehose__processor.firehose_subscription
  ]
  handler = "api.consumer.authoriser.index.handler"
  depends_on = [
  ]
}

module "consumer__status" {
  source                 = "./modules/lambda"
  parent_path            = "api/consumer"
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
    SPLUNK_INDEX                = module.firehose__processor.splunk.index
    DYNAMODB_TIMEOUT            = local.dynamodb_timeout_seconds
  }
  additional_policies = [
    aws_iam_policy.document-pointer__dynamodb-read.arn,
    aws_iam_policy.document-pointer__kms-read-write.arn
  ]
  firehose_subscriptions = [
    module.firehose__processor.firehose_subscription
  ]
  handler = "api.consumer.status.index.handler"
}


module "producer__status" {
  source                 = "./modules/lambda"
  parent_path            = "api/producer"
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
    SPLUNK_INDEX                = module.firehose__processor.splunk.index
    DYNAMODB_TIMEOUT            = local.dynamodb_timeout_seconds
  }
  additional_policies = [
    aws_iam_policy.document-pointer__dynamodb-read.arn,
    aws_iam_policy.document-pointer__kms-read-write.arn
  ]
  firehose_subscriptions = [
    module.firehose__processor.firehose_subscription
  ]
  handler = "api.producer.status.index.handler"
}
