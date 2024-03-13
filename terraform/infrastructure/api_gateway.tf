module "consumer__gateway" {
  source  = "./modules/api_gateway"
  apitype = "consumer"
  prefix  = local.prefix
  lambdas = {
    environment                        = terraform.workspace
    method_countDocumentReference      = "arn:aws:apigateway:eu-west-2:lambda:path/2015-03-31/functions/arn:aws:lambda:eu-west-2:${var.assume_account}:function:${substr("${local.prefix}--api--consumer--countDocumentReference", 0, 64)}/invocations"
    method_searchDocumentReference     = "arn:aws:apigateway:eu-west-2:lambda:path/2015-03-31/functions/arn:aws:lambda:eu-west-2:${var.assume_account}:function:${substr("${local.prefix}--api--consumer--searchDocumentReference", 0, 64)}//invocations"
    method_searchPostDocumentReference = "arn:aws:apigateway:eu-west-2:lambda:path/2015-03-31/functions/arn:aws:lambda:eu-west-2:${var.assume_account}:function:${substr("${local.prefix}--api--consumer--searchPostDocumentReference", 0, 64)}/invocations"
    method_readDocumentReference       = "arn:aws:apigateway:eu-west-2:lambda:path/2015-03-31/functions/arn:aws:lambda:eu-west-2:${var.assume_account}:function:${substr("${local.prefix}--api--consumer--readDocumentReference", 0, 64)}/invocations"
    method_status                      = "arn:aws:apigateway:eu-west-2:lambda:path/2015-03-31/functions/arn:aws:lambda:eu-west-2:${var.assume_account}:function:${substr("${local.prefix}--api--consumer--status", 0, 64)}/invocations"
  }
  kms_key_id                   = module.kms__cloudwatch.kms_arn
  authoriser_lambda_invoke_arn = module.consumer__authoriser_lambda.invoke_arn
  authoriser_lambda_arn        = module.consumer__authoriser_lambda.arn
  domain                       = local.apis.domain
  path                         = local.apis.consumer.path
  capability_statement_content = templatefile("${path.module}/consumer.tftpl", { domain = local.public_domain, id = filesha1("${path.module}/consumer.tftpl") })
  depends_on = [
    aws_acm_certificate_validation.validation
  ]
}

module "producer__gateway" {
  source  = "./modules/api_gateway"
  apitype = "producer"
  prefix  = local.prefix
  lambdas = {
    environment                        = terraform.workspace
    method_searchDocumentReference     = "arn:aws:apigateway:eu-west-2:lambda:path/2015-03-31/functions/arn:aws:lambda:eu-west-2:${var.assume_account}:function:${substr("${local.prefix}--api--producer--searchDocumentReference", 0, 64)}/invocations"
    method_searchPostDocumentReference = "arn:aws:apigateway:eu-west-2:lambda:path/2015-03-31/functions/arn:aws:lambda:eu-west-2:${var.assume_account}:function:${substr("${local.prefix}--api--producer--searchPostDocumentReference", 0, 64)}/invocations"
    method_readDocumentReference       = "arn:aws:apigateway:eu-west-2:lambda:path/2015-03-31/functions/arn:aws:lambda:eu-west-2:${var.assume_account}:function:${substr("${local.prefix}--api--producer--readDocumentReference", 0, 64)}/invocations"
    method_createDocumentReference     = "arn:aws:apigateway:eu-west-2:lambda:path/2015-03-31/functions/arn:aws:lambda:eu-west-2:${var.assume_account}:function:${substr("${local.prefix}--api--producer--createDocumentReference", 0, 64)}/invocations"
    method_updateDocumentReference     = "arn:aws:apigateway:eu-west-2:lambda:path/2015-03-31/functions/arn:aws:lambda:eu-west-2:${var.assume_account}:function:${substr("${local.prefix}--api--producer--updateDocumentReference", 0, 64)}/invocations"
    method_upsertDocumentReference     = "arn:aws:apigateway:eu-west-2:lambda:path/2015-03-31/functions/arn:aws:lambda:eu-west-2:${var.assume_account}:function:${substr("${local.prefix}--api--producer--upsertDocumentReference", 0, 64)}/invocations"
    method_deleteDocumentReference     = "arn:aws:apigateway:eu-west-2:lambda:path/2015-03-31/functions/arn:aws:lambda:eu-west-2:${var.assume_account}:function:${substr("${local.prefix}--api--producer--deleteDocumentReference", 0, 64)}/invocations"
    method_status                      = "arn:aws:apigateway:eu-west-2:lambda:path/2015-03-31/functions/arn:aws:lambda:eu-west-2:${var.assume_account}:function:${substr("${local.prefix}--api--producer--status", 0, 64)}/invocations"
  }
  kms_key_id                   = module.kms__cloudwatch.kms_arn
  authoriser_lambda_invoke_arn = module.producer__authoriser_lambda.invoke_arn
  authoriser_lambda_arn        = module.producer__authoriser_lambda.arn
  domain                       = local.apis.domain
  path                         = local.apis.producer.path
  capability_statement_content = templatefile("${path.module}/producer.tftpl", { domain = local.public_domain, id = filesha1("${path.module}/producer.tftpl") })
  depends_on = [
    aws_acm_certificate_validation.validation
  ]
}
