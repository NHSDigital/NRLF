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
    echo "  destroy-non-mgmt               - Destroys a workspace completely in non-mgmt (Dev) account. ONLY USE IF TERRAFORM DESTROY HAS NOT COMPLETED"
    echo
    return 1
}

function _check_mgmt() {
  if [[ "$(aws iam list-account-aliases --query 'AccountAliases[0]' --output text)"] != 'nhsd-nrlf-mgmt' ]]; then
    echo "Please log in as the mgmt account" >&2
    return 1
  fi
}

function _check_non_mgmt() {
    if [[ "$(aws iam list-account-aliases --query 'AccountAliases[0]' --output text)"] != 'nhsd-nrlf-mgmt' ]]; then
    echo "Please log in as a non-mgmt account" >&2
    return 1
  fi
}

function _get_mgmt_account(){
  if ! _check_mgmt; then return 1; fi
  return $(aws sts get-caller-identity --query Account --output text)
}


function _bootstrap() {
  local command=$1
  local admin_policy_arn="arn:aws:iam::aws:policy/AdministratorAccess"
  local truststore_bucket_name="${PROFILE_PREFIX}--truststore"
  local state_bucket_name="${PROFILE_PREFIX}--terraform-state"
  local state_lock_table_name="${PROFILE_PREFIX}--terraform-state-lock"

  case $command in
    "create-mgmt")
      _check_mgmt || return 1

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
      _check_mgmt || return 1

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
      _check_non_mgmt || return 1

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
      _check_non_mgmt || return 1

      aws iam detach-role-policy --policy-arn "${admin_policy_arn}" --role-name "${TERRAFORM_ROLE_NAME}" || return 1
      aws iam delete-role --role-name "${TERRAFORM_ROLE_NAME}" || return 1
      echo "Deleted role ${TERRAFORM_ROLE_NAME} and associated policy ${admin_policy_arn}"
    ;;
    #----------------
    "destroy-non-mgmt")
      _check_non_mgmt || return 1
      # TODO: Reintroduce the admin check - but should be fine for all developers
      # if [[ "$(aws sts get-caller-identity)" != *dev* || "$(aws sts get-caller-identity)" != *NHSDAdminRole* ]]; then
      #     echo "Please log in as dev with an Admin account" >&2
      #     return 1
      # fi

      local workspace
      workspace=$2
      # Fetch the resources using the AWS CLI command
      aws resourcegroupstaggingapi get-resources --tag-filters Key=workspace,Values="$2" | jq -c '.ResourceTagMappingList[]' |
      while IFS= read -r item; do
          arn=$(jq -r '.ResourceARN' <<< "$item")

          case $arn in
              arn:aws:lambda* )
                  echo "Deleting... : $arn"
                  aws lambda delete-function --function-name $arn
                  ;;
              arn:aws:kms* )
                  echo "Disabling... : $arn"
                  aws kms disable-key --key-id $arn
                  echo "Deleting... ': $arn"
                  aws kms schedule-key-deletion --key-id $arn --pending-window-in-days 7
                  ;;
              arn:aws:logs* )
                  echo "Deleting... : $arn"
                  new_var=$(echo "$arn" | awk -F':' '{print $NF}')
                  aws logs delete-log-group --log-group-name $new_var
                  ;;
              arn:aws:secretsmanager* )
                  echo "Deleting... : $arn"
                  aws secretsmanager delete-secret --secret-id $arn
                  ;;
              arn:aws:apigateway* )
                    echo "Deleting domain-name... : $workspace"
                    aws apigateway delete-domain-name --domain-name "$workspace.api.record-locator.dev.national.nhs.uk"
                    echo "Deleting... : $arn"
                    ag_id=$(echo "$arn" | awk -F'/restapis/' '{print $2}' | awk -F'/' '{print $1}')
                    aws apigateway delete-rest-api --rest-api-id $ag_id
                  ;;
              arn:aws:dynamodb* )
                  echo "Deleting... : $arn"
                  new_var=$(echo "$arn" | awk -F':' '{print $NF}')
                  table=$(echo "$arn" | awk -F'/' '{print $NF}')
                  aws dynamodb delete-table --table-name $table
                  ;;
              arn:aws:s3* )
                  echo "Deleting... : $arn"
                  new_var=$(echo "$arn" | awk -F':' '{print $NF}')
                  local versioned_objects
                  versioned_objects=$(aws s3api list-object-versions \
                                      --bucket "${new_var}" \
                                      --output=json \
                                      --query='{Objects: Versions[].{Key:Key,VersionId:VersionId}}') || return 1
                  aws s3api delete-objects \
                      --bucket "${new_var}" \
                      --delete "${versioned_objects}" || echo "Ignore the previous warning - an empty bucket is a good thing"
                  echo "Waiting for bucket contents to be deleted..." && sleep 10
                  aws s3 rb "s3://${new_var}" --force || echo "Bucket could not be deleted at this time. You should go to the AWS Console and delete the bucket manually."
                  ;;
              arn:aws:ssm* )
                  echo "Deleting... : $arn"
                  new_var=$(echo "$arn" | awk -F':' '{print $NF}')
                  suffix=$(echo "$arn" | awk -F'/' '{print $NF}')
                  name=$(echo "$new_var" | awk -F'/' '{print $(NF-1)}')
                  aws ssm delete-parameter --name $name/$suffix
                  ;;
              arn:aws:acm* )
                  echo "Deleting... : $arn"
                  aws acm delete-certificate --certificate-arn $arn
                  ;;
              arn:aws:firehose* )
                  echo "Deleting... : $arn"
                  new_var=$(echo "$arn" | awk -F':' '{print $NF}')
                  name=$(echo "$new_var" | awk -F'/' '{print $NF}')
                  aws firehose delete-delivery-stream --delivery-stream-name $name
                  ;;
              * )
                  echo "Unknown ARN type: $arn"
                  ;;
          esac
      done
    ;;
    #----------------
    *) _bootstrap_help ;;
    esac
}
