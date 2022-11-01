module "consumer__gateway" {
  source  = "./modules/api_gateway"
  apitype = "consumer"
  prefix  = local.prefix
  lambdas = {
    environment                           = terraform.workspace
    method_searchDocumentReference        = "arn:aws:apigateway:eu-west-2:lambda:path/2015-03-31/functions/arn:aws:lambda:eu-west-2:${var.assume_account}:function:${local.prefix}--api--consumer--searchDocumentReference/invocations"
    method_searchViaPostDocumentReference = "arn:aws:apigateway:eu-west-2:lambda:path/2015-03-31/functions/arn:aws:lambda:eu-west-2:${var.assume_account}:function:${local.prefix}--api--consumer--searchViaPostDocumentReference/invocations"
    method_readDocumentReference          = "arn:aws:apigateway:eu-west-2:lambda:path/2015-03-31/functions/arn:aws:lambda:eu-west-2:${var.assume_account}:function:${local.prefix}--api--consumer--readDocumentReference/invocations"
  }
  kms_key_id = module.kms__cloudwatch.kms_arn
}

module "producer__gateway" {
  source  = "./modules/api_gateway"
  apitype = "producer"
  prefix  = local.prefix
  lambdas = {
    environment                    = terraform.workspace
    method_searchDocumentReference = "arn:aws:apigateway:eu-west-2:lambda:path/2015-03-31/functions/arn:aws:lambda:eu-west-2:${var.assume_account}:function:${local.prefix}--api--producer--searchDocumentReference/invocations"
    method_readDocumentReference   = "arn:aws:apigateway:eu-west-2:lambda:path/2015-03-31/functions/arn:aws:lambda:eu-west-2:${var.assume_account}:function:${local.prefix}--api--producer--readDocumentReference/invocations"
    method_createDocumentReference = "arn:aws:apigateway:eu-west-2:lambda:path/2015-03-31/functions/arn:aws:lambda:eu-west-2:${var.assume_account}:function:${local.prefix}--api--producer--createDocumentReference/invocations"
    method_updateDocumentReference = "arn:aws:apigateway:eu-west-2:lambda:path/2015-03-31/functions/arn:aws:lambda:eu-west-2:${var.assume_account}:function:${local.prefix}--api--producer--updateDocumentReference/invocations"
    method_deleteDocumentReference = "arn:aws:apigateway:eu-west-2:lambda:path/2015-03-31/functions/arn:aws:lambda:eu-west-2:${var.assume_account}:function:${local.prefix}--api--producer--deleteDocumentReference/invocations"
  }
  kms_key_id = module.kms__cloudwatch.kms_arn
}
