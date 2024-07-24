module "consumer__readDocumentReference" {
  source                 = "./modules/lambda"
  parent_path            = "api/consumer"
  name                   = "readDocumentReference"
  region                 = local.region
  prefix                 = local.prefix
  layers                 = [module.nrlf.layer_arn, module.third_party.layer_arn, module.nrlf_permissions.layer_arn]
  api_gateway_source_arn = ["arn:aws:execute-api:${local.region}:${local.aws_account_id}:${module.consumer__gateway.api_gateway_id}/*/GET/DocumentReference/{id}"]
  kms_key_id             = module.kms__cloudwatch.kms_arn
  environment_variables = {
    PREFIX               = "${local.prefix}--"
    ENVIRONMENT          = local.environment
    POWERTOOLS_LOG_LEVEL = local.log_level
    SPLUNK_INDEX         = module.firehose__processor.splunk.index
    AUTH_STORE           = local.auth_store_id
    TABLE_NAME           = local.pointers_table_name
  }
  additional_policies = [
    local.pointers_table_read_policy_arn,
    local.pointers_kms_read_write_arn,
    local.auth_store_read_policy_arn
  ]
  firehose_subscriptions = [
    module.firehose__processor.firehose_subscription
  ]
  handler   = "read_document_reference.handler"
  retention = local.is_ephemeral ? 90 : 15
}

module "consumer__countDocumentReference" {
  source                 = "./modules/lambda"
  parent_path            = "api/consumer"
  name                   = "countDocumentReference"
  region                 = local.region
  prefix                 = local.prefix
  layers                 = [module.nrlf.layer_arn, module.third_party.layer_arn, module.nrlf_permissions.layer_arn]
  api_gateway_source_arn = ["arn:aws:execute-api:${local.region}:${local.aws_account_id}:${module.consumer__gateway.api_gateway_id}/*/GET/DocumentReference/_count"]
  kms_key_id             = module.kms__cloudwatch.kms_arn
  environment_variables = {
    PREFIX               = "${local.prefix}--"
    ENVIRONMENT          = local.environment
    AUTH_STORE           = local.auth_store_id
    POWERTOOLS_LOG_LEVEL = local.log_level
    SPLUNK_INDEX         = module.firehose__processor.splunk.index
    TABLE_NAME           = local.pointers_table_name
  }
  additional_policies = [
    local.pointers_table_read_policy_arn,
    local.pointers_kms_read_write_arn,
    local.auth_store_read_policy_arn
  ]
  firehose_subscriptions = [
    module.firehose__processor.firehose_subscription
  ]
  handler   = "count_document_reference.handler"
  retention = local.is_ephemeral ? 90 : 15

}

module "consumer__searchDocumentReference" {
  source                 = "./modules/lambda"
  parent_path            = "api/consumer"
  name                   = "searchDocumentReference"
  region                 = local.region
  prefix                 = local.prefix
  layers                 = [module.nrlf.layer_arn, module.third_party.layer_arn, module.nrlf_permissions.layer_arn]
  api_gateway_source_arn = ["arn:aws:execute-api:${local.region}:${local.aws_account_id}:${module.consumer__gateway.api_gateway_id}/*/GET/DocumentReference"]
  kms_key_id             = module.kms__cloudwatch.kms_arn
  environment_variables = {
    PREFIX               = "${local.prefix}--"
    ENVIRONMENT          = local.environment
    AUTH_STORE           = local.auth_store_id
    POWERTOOLS_LOG_LEVEL = local.log_level
    SPLUNK_INDEX         = module.firehose__processor.splunk.index
    TABLE_NAME           = local.pointers_table_name
  }
  additional_policies = [
    local.pointers_table_read_policy_arn,
    local.pointers_kms_read_write_arn,
    local.auth_store_read_policy_arn
  ]
  firehose_subscriptions = [
    module.firehose__processor.firehose_subscription
  ]
  handler   = "search_document_reference.handler"
  retention = local.is_ephemeral ? 90 : 15
}

module "consumer__searchPostDocumentReference" {
  source                 = "./modules/lambda"
  parent_path            = "api/consumer"
  name                   = "searchPostDocumentReference"
  region                 = local.region
  prefix                 = local.prefix
  layers                 = [module.nrlf.layer_arn, module.third_party.layer_arn, module.nrlf_permissions.layer_arn]
  api_gateway_source_arn = ["arn:aws:execute-api:${local.region}:${local.aws_account_id}:${module.consumer__gateway.api_gateway_id}/*/POST/DocumentReference/_search"]
  kms_key_id             = module.kms__cloudwatch.kms_arn
  environment_variables = {
    PREFIX               = "${local.prefix}--"
    ENVIRONMENT          = local.environment
    AUTH_STORE           = local.auth_store_id
    POWERTOOLS_LOG_LEVEL = local.log_level
    SPLUNK_INDEX         = module.firehose__processor.splunk.index
    TABLE_NAME           = local.pointers_table_name
  }
  additional_policies = [
    local.pointers_table_read_policy_arn,
    local.pointers_kms_read_write_arn,
    local.auth_store_read_policy_arn
  ]
  firehose_subscriptions = [
    module.firehose__processor.firehose_subscription
  ]
  handler   = "search_post_document_reference.handler"
  retention = local.is_ephemeral ? 90 : 15
}

module "producer__createDocumentReference" {
  source                 = "./modules/lambda"
  parent_path            = "api/producer"
  name                   = "createDocumentReference"
  region                 = local.region
  prefix                 = local.prefix
  layers                 = [module.nrlf.layer_arn, module.third_party.layer_arn, module.nrlf_permissions.layer_arn]
  api_gateway_source_arn = ["arn:aws:execute-api:${local.region}:${local.aws_account_id}:${module.producer__gateway.api_gateway_id}/*/POST/DocumentReference"]
  kms_key_id             = module.kms__cloudwatch.kms_arn
  environment_variables = {
    PREFIX               = "${local.prefix}--"
    ENVIRONMENT          = local.environment
    AUTH_STORE           = local.auth_store_id
    SPLUNK_INDEX         = module.firehose__processor.splunk.index
    POWERTOOLS_LOG_LEVEL = local.log_level
    TABLE_NAME           = local.pointers_table_name
  }
  additional_policies = [
    local.pointers_table_write_policy_arn,
    local.pointers_table_read_policy_arn,
    local.pointers_kms_read_write_arn,
    local.auth_store_read_policy_arn
  ]
  firehose_subscriptions = [
    module.firehose__processor.firehose_subscription
  ]
  handler   = "create_document_reference.handler"
  retention = local.is_ephemeral ? 90 : 15
}

module "producer__deleteDocumentReference" {
  source                 = "./modules/lambda"
  parent_path            = "api/producer"
  name                   = "deleteDocumentReference"
  region                 = local.region
  prefix                 = local.prefix
  layers                 = [module.nrlf.layer_arn, module.third_party.layer_arn, module.nrlf_permissions.layer_arn]
  api_gateway_source_arn = ["arn:aws:execute-api:${local.region}:${local.aws_account_id}:${module.producer__gateway.api_gateway_id}/*/DELETE/DocumentReference/{id}"]
  kms_key_id             = module.kms__cloudwatch.kms_arn
  environment_variables = {
    PREFIX               = "${local.prefix}--"
    ENVIRONMENT          = local.environment
    AUTH_STORE           = local.auth_store_id
    POWERTOOLS_LOG_LEVEL = local.log_level
    SPLUNK_INDEX         = module.firehose__processor.splunk.index
    TABLE_NAME           = local.pointers_table_name
  }
  additional_policies = [
    local.pointers_table_write_policy_arn,
    local.pointers_table_read_policy_arn,
    local.pointers_kms_read_write_arn,
    local.auth_store_read_policy_arn
  ]
  firehose_subscriptions = [
    module.firehose__processor.firehose_subscription
  ]
  handler   = "delete_document_reference.handler"
  retention = local.is_ephemeral ? 90 : 15
}

module "producer__readDocumentReference" {
  source                 = "./modules/lambda"
  parent_path            = "api/producer"
  name                   = "readDocumentReference"
  region                 = local.region
  prefix                 = local.prefix
  layers                 = [module.nrlf.layer_arn, module.third_party.layer_arn, module.nrlf_permissions.layer_arn]
  api_gateway_source_arn = ["arn:aws:execute-api:${local.region}:${local.aws_account_id}:${module.producer__gateway.api_gateway_id}/*/GET/DocumentReference/{id}"]
  kms_key_id             = module.kms__cloudwatch.kms_arn
  environment_variables = {
    PREFIX               = "${local.prefix}--"
    ENVIRONMENT          = local.environment
    AUTH_STORE           = local.auth_store_id
    POWERTOOLS_LOG_LEVEL = local.log_level
    SPLUNK_INDEX         = module.firehose__processor.splunk.index
    TABLE_NAME           = local.pointers_table_name
  }
  additional_policies = [
    local.pointers_table_read_policy_arn,
    local.pointers_kms_read_write_arn,
    local.auth_store_read_policy_arn
  ]
  firehose_subscriptions = [
    module.firehose__processor.firehose_subscription
  ]
  handler   = "read_document_reference.handler"
  retention = local.is_ephemeral ? 90 : 15
}

module "producer__searchDocumentReference" {
  source                 = "./modules/lambda"
  parent_path            = "api/producer"
  name                   = "searchDocumentReference"
  region                 = local.region
  prefix                 = local.prefix
  layers                 = [module.nrlf.layer_arn, module.third_party.layer_arn, module.nrlf_permissions.layer_arn]
  api_gateway_source_arn = ["arn:aws:execute-api:${local.region}:${local.aws_account_id}:${module.producer__gateway.api_gateway_id}/*/GET/DocumentReference"]
  kms_key_id             = module.kms__cloudwatch.kms_arn
  environment_variables = {
    PREFIX               = "${local.prefix}--"
    ENVIRONMENT          = local.environment
    AUTH_STORE           = local.auth_store_id
    POWERTOOLS_LOG_LEVEL = local.log_level
    SPLUNK_INDEX         = module.firehose__processor.splunk.index
    TABLE_NAME           = local.pointers_table_name
  }
  additional_policies = [
    local.pointers_table_read_policy_arn,
    local.pointers_kms_read_write_arn,
    local.auth_store_read_policy_arn
  ]
  firehose_subscriptions = [
    module.firehose__processor.firehose_subscription
  ]
  handler   = "search_document_reference.handler"
  retention = local.is_ephemeral ? 90 : 15
}

module "producer__searchPostDocumentReference" {
  source                 = "./modules/lambda"
  parent_path            = "api/producer"
  name                   = "searchPostDocumentReference"
  region                 = local.region
  prefix                 = local.prefix
  layers                 = [module.nrlf.layer_arn, module.third_party.layer_arn, module.nrlf_permissions.layer_arn]
  api_gateway_source_arn = ["arn:aws:execute-api:${local.region}:${local.aws_account_id}:${module.producer__gateway.api_gateway_id}/*/POST/DocumentReference/_search"]
  kms_key_id             = module.kms__cloudwatch.kms_arn
  environment_variables = {
    PREFIX               = "${local.prefix}--"
    ENVIRONMENT          = local.environment
    AUTH_STORE           = local.auth_store_id
    POWERTOOLS_LOG_LEVEL = local.log_level
    SPLUNK_INDEX         = module.firehose__processor.splunk.index
    TABLE_NAME           = local.pointers_table_name
  }
  additional_policies = [
    local.pointers_table_read_policy_arn,
    local.pointers_kms_read_write_arn,
    local.auth_store_read_policy_arn
  ]
  firehose_subscriptions = [
    module.firehose__processor.firehose_subscription
  ]
  handler   = "search_post_document_reference.handler"
  retention = local.is_ephemeral ? 90 : 15
}

module "producer__updateDocumentReference" {
  source                 = "./modules/lambda"
  parent_path            = "api/producer"
  name                   = "updateDocumentReference"
  region                 = local.region
  prefix                 = local.prefix
  layers                 = [module.nrlf.layer_arn, module.third_party.layer_arn, module.nrlf_permissions.layer_arn]
  api_gateway_source_arn = ["arn:aws:execute-api:${local.region}:${local.aws_account_id}:${module.producer__gateway.api_gateway_id}/*/PUT/DocumentReference/{id}"]
  kms_key_id             = module.kms__cloudwatch.kms_arn
  environment_variables = {
    PREFIX               = "${local.prefix}--"
    ENVIRONMENT          = local.environment
    AUTH_STORE           = local.auth_store_id
    POWERTOOLS_LOG_LEVEL = local.log_level
    SPLUNK_INDEX         = module.firehose__processor.splunk.index
    TABLE_NAME           = local.pointers_table_name
  }
  additional_policies = [
    local.pointers_table_read_policy_arn,
    local.pointers_table_write_policy_arn,
    local.pointers_kms_read_write_arn,
    local.auth_store_read_policy_arn
  ]
  firehose_subscriptions = [
    module.firehose__processor.firehose_subscription
  ]
  handler   = "update_document_reference.handler"
  retention = local.is_ephemeral ? 90 : 15
}

module "producer__upsertDocumentReference" {
  source                 = "./modules/lambda"
  parent_path            = "api/producer"
  name                   = "upsertDocumentReference"
  region                 = local.region
  prefix                 = local.prefix
  layers                 = [module.nrlf.layer_arn, module.third_party.layer_arn, module.nrlf_permissions.layer_arn]
  api_gateway_source_arn = ["arn:aws:execute-api:${local.region}:${local.aws_account_id}:${module.producer__gateway.api_gateway_id}/*/PUT/DocumentReference"]
  kms_key_id             = module.kms__cloudwatch.kms_arn
  environment_variables = {
    PREFIX               = "${local.prefix}--"
    ENVIRONMENT          = local.environment
    AUTH_STORE           = local.auth_store_id
    POWERTOOLS_LOG_LEVEL = local.log_level
    SPLUNK_INDEX         = module.firehose__processor.splunk.index
    TABLE_NAME           = local.pointers_table_name
  }
  additional_policies = [
    local.pointers_table_write_policy_arn,
    local.pointers_table_read_policy_arn,
    local.pointers_kms_read_write_arn,
    local.auth_store_read_policy_arn
  ]
  firehose_subscriptions = [
    module.firehose__processor.firehose_subscription
  ]
  handler   = "upsert_document_reference.handler"
  retention = local.is_ephemeral ? 90 : 15
}

module "consumer__status" {
  source                 = "./modules/lambda"
  parent_path            = "api/consumer"
  name                   = "status"
  region                 = local.region
  prefix                 = local.prefix
  layers                 = [module.nrlf.layer_arn, module.third_party.layer_arn, module.nrlf_permissions.layer_arn]
  api_gateway_source_arn = ["arn:aws:execute-api:${local.region}:${local.aws_account_id}:${module.consumer__gateway.api_gateway_id}/*/GET/_status"]
  kms_key_id             = module.kms__cloudwatch.kms_arn
  environment_variables = {
    PREFIX               = "${local.prefix}--"
    ENVIRONMENT          = local.environment
    AUTH_STORE           = local.auth_store_id
    POWERTOOLS_LOG_LEVEL = local.log_level
    SPLUNK_INDEX         = module.firehose__processor.splunk.index
    DYNAMODB_TIMEOUT     = local.dynamodb_timeout_seconds
    TABLE_NAME           = local.pointers_table_name
  }
  additional_policies = [
    local.pointers_table_read_policy_arn,
    local.pointers_kms_read_write_arn,
    local.auth_store_read_policy_arn
  ]
  firehose_subscriptions = [
    module.firehose__processor.firehose_subscription
  ]
  handler   = "status.handler"
  retention = local.is_ephemeral ? 90 : 15
}


module "producer__status" {
  source                 = "./modules/lambda"
  parent_path            = "api/producer"
  name                   = "status"
  region                 = local.region
  prefix                 = local.prefix
  layers                 = [module.nrlf.layer_arn, module.third_party.layer_arn, module.nrlf_permissions.layer_arn]
  api_gateway_source_arn = ["arn:aws:execute-api:${local.region}:${local.aws_account_id}:${module.producer__gateway.api_gateway_id}/*/GET/_status"]
  kms_key_id             = module.kms__cloudwatch.kms_arn
  environment_variables = {
    PREFIX               = "${local.prefix}--"
    ENVIRONMENT          = local.environment
    AUTH_STORE           = local.auth_store_id
    POWERTOOLS_LOG_LEVEL = local.log_level
    SPLUNK_INDEX         = module.firehose__processor.splunk.index
    DYNAMODB_TIMEOUT     = local.dynamodb_timeout_seconds
    TABLE_NAME           = local.pointers_table_name
  }
  additional_policies = [
    local.pointers_table_read_policy_arn,
    local.pointers_kms_read_write_arn,
    local.auth_store_read_policy_arn
  ]
  firehose_subscriptions = [
    module.firehose__processor.firehose_subscription
  ]
  handler   = "status.handler"
  retention = local.is_ephemeral ? 90 : 15
}
