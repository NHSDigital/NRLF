#!/bin/bash

PROFILE_PREFIX="nhsd-nrlf"
AWS_REGION_NAME="eu-west-2"
TERRAFORM_ROLE_NAME="NHSDTerraformRole"
MGMT_ACCOUNT_ID_LOCATION="${PROFILE_PREFIX}--mgmt--mgmt-account-id"
PROD_ACCOUNT_ID_LOCATION="${PROFILE_PREFIX}--mgmt--prod-account-id"
TEST_ACCOUNT_ID_LOCATION="${PROFILE_PREFIX}--mgmt--test-account-id"
DEV_ACCOUNT_ID_LOCATION="${PROFILE_PREFIX}--mgmt--dev-account-id"
