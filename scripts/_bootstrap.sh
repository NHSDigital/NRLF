#!/bin/bash

function _bootstrap_help() {
    echo
    echo "nrlf bootstrap <command> [options]"
    echo
    echo "commands:"
    echo "  help                           - this help screen"
    echo "  create-mgmt                    - Creates required aws resource for terraform access in mgmt account"
    echo "  delete-mgmt                    - Deletes required aws resource for terraform access in mgmt account"
    echo "  create-non-mgmt                - Creates required aws resource for terraform access in non-mgmt account"
    echo "  delete-non-mgmt                - Deletes required aws resource for terraform access in non-mgmt account"
    echo
    return 1
}


function _get_mgmt_account(){
  python -c "import os; from configparser import ConfigParser; parser = ConfigParser(); parser.read(os.environ['HOME'] + '/.aws/config'); print(parser['nhsd-nrlf-mgmt-admin']['aws_account_id'])"
  return $?
}


function _bootstrap() {
  local command=$1
  local admin_policy_arn="arn:aws:iam::aws:policy/AdministratorAccess"
  local truststore_bucket_name="${PROFILE_PREFIX}--truststore"
  local state_bucket_name="${PROFILE_PREFIX}--terraform-state"
  local state_lock_table_name="${PROFILE_PREFIX}--terraform-state-lock"

  case $command in
    "create-mgmt")
      if [[ "$(aws sts get-caller-identity)" != *mgmt* ]]; then
          echo "Please log in as the mgmt account" >&2
          return 1
      fi

      cd $root/terraform/bootstrap/mgmt
      aws s3api create-bucket --bucket "${truststore_bucket_name}" --region us-east-1 --create-bucket-configuration LocationConstraint="${AWS_REGION_NAME}"
      aws s3api create-bucket --bucket "${state_bucket_name}" --region us-east-1 --create-bucket-configuration LocationConstraint="${AWS_REGION_NAME}"
      aws s3api put-public-access-block --bucket "${state_bucket_name}" --public-access-block-configuration "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"
      aws dynamodb create-table --cli-input-json file://locktable.json --region "${AWS_REGION_NAME}"
      aws secretsmanager create-secret --name "${MGMT_ACCOUNT_ID_LOCATION}"
      aws secretsmanager create-secret --name "${DEV_ACCOUNT_ID_LOCATION}"
      aws secretsmanager create-secret --name "${TEST_ACCOUNT_ID_LOCATION}"
      aws secretsmanager create-secret --name "${PROD_ACCOUNT_ID_LOCATION}"
    ;;
    #----------------
    "delete-mgmt")
      if [[ "$(aws sts get-caller-identity)" != *mgmt* ]]; then
          echo "Please log in as the mgmt account" >&2
          return 1
      fi

      cd $root/terraform/bootstrap/mgmt
      aws dynamodb delete-table --table-name "${state_lock_table_name}" || return 1
      local versioned_objects
      versioned_objects=$(aws s3api list-object-versions \
                          --bucket "${state_bucket_name}" \
                          --output=json \
                          --query='{Objects: Versions[].{Key:Key,VersionId:VersionId}}') || return 1
      aws s3api delete-objects \
          --bucket "${state_bucket_name}" \
          --delete "${versioned_objects}" || echo "Ignore the previous warning - an empty bucket is a good thing"
      echo "Waiting for bucket contents to be deleted..." && sleep 10
      aws s3 rb "s3://${state_bucket_name}" || echo "Bucket could not be deleted at this time. You should go to the AWS Console and delete the bucket manually."
      aws secretsmanager delete-secret --secret-id "${MGMT_ACCOUNT_ID_LOCATION}"
      aws secretsmanager delete-secret --secret-id "${DEV_ACCOUNT_ID_LOCATION}"
      aws secretsmanager delete-secret --secret-id "${TEST_ACCOUNT_ID_LOCATION}"
      aws secretsmanager delete-secret --secret-id "${PROD_ACCOUNT_ID_LOCATION}"
    ;;
    #----------------
    "create-non-mgmt")
      if [[ "$(aws sts get-caller-identity)" == *mgmt* ]]; then
          echo "Please log in as a non-mgmt account" >&2
          return 1
      fi

      cd $root/terraform/bootstrap/non-mgmt
      local tf_assume_role_policy
      local mgmt_account_id
      mgmt_account_id=$(_get_mgmt_account)
      tf_assume_role_policy=$(awk "{sub(/REPLACEME/,\"${mgmt_account_id}\")}1" terraform-trust-policy.json)
      aws iam create-role --role-name "${TERRAFORM_ROLE_NAME}" --assume-role-policy-document "${tf_assume_role_policy}" || return 1
      aws iam attach-role-policy --policy-arn "${admin_policy_arn}" --role-name "${TERRAFORM_ROLE_NAME}" || return 1
      ;;
    #----------------
    "delete-non-mgmt")
      if [[ "$(aws sts get-caller-identity)" == *mgmt* ]]; then
          echo "Please log in as a non-mgmt account" >&2
          return 1
      fi

      aws iam detach-role-policy --policy-arn "${admin_policy_arn}" --role-name "${TERRAFORM_ROLE_NAME}" || return 1
      aws iam delete-role --role-name "${TERRAFORM_ROLE_NAME}" || return 1
      echo "Deleted role ${TERRAFORM_ROLE_NAME} and associated policy ${admin_policy_arn}"
    ;;
    #----------------
    *) _bootstrap_help ;;
    esac
}
