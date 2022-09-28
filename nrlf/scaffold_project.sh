#!/bin/bash

yo aws-api:app nrlf \
    python \
    eu-west-2 \
    nrlf-terraform-state \
    nrlf-terraform-state-lock \
    483433329243 mgmt NHSDAdminRole \
    295962215401 terraform NHSDAdminRole\
    295962215401 terraform NHSDAdminRole\
    295962215401 terraform NHSDAdminRole

yo aws-api:layer nrlf python
yo aws-api:layer lambda-utils python
yo aws-api:layer third-party python yes

yo aws-api:kms-base
yo aws-api:kms cloudwatch "Cloudwatch log KMS key" "eu-west-2" "yes"
yo aws-api:kms document-reference "Document reference table KMS key" "eu-west-2" "no"
yo aws-api:kms custodian "Custodian table KMS key" "eu-west-2" "no"

yo aws-api:lambda-base
yo aws-api:api-swagger "eu-west-2" producer "swagger/producer.yaml" "post /DocumentReference,put /DocumentReference/{id},delete /DocumentReference/{id}" python "(none)" "nrlf,lambda-utils,third-party" "cloudwatch"
yo aws-api:api-swagger "eu-west-2" consumer "swagger/consumer.yaml" "get /DocumentReference,post /DocumentReference/_search,get /DocumentReference/{id}" python "(none)" "nrlf,lambda-utils,third-party" "cloudwatch"

yo aws-api:dynamodb document-reference "nhs_number" "S" "" "" "" PAY_PER_REQUEST "" "" "document-reference"
yo aws-api:dynamodb custodian "ods_code" "S" "" "" "" PAY_PER_REQUEST "" "" "custodian"


# yo aws-api:account-wide-terraform nrlf \
#     eu-west-2 \
#     nrlf-terraform-state \
#     nrlf-terraform-state-lock \
#     483433329243 mgmt NHSDAdminRole \
#     295962215401 terraform NHSDAdminRole\
#     295962215401 terraform NHSDAdminRole\
#     295962215401 terraform NHSDAdminRole