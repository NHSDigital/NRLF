#!/bin/bash

function _bootstrap_help() {
    echo
    echo "nrlf bootstrap <command> [options]"
    echo
    echo "commands:"
    echo "  help                           - this help screen"
    echo "  create-mgmt-state              - Creates terraform state files in the mgmt account"
    echo "  delete-mgmt-state              - Deletes terraform state files in the mgmt account"
    echo "  create-terraform-role-non-mgmt - Creates terraform role in the current non-mgmt account"
    echo "  delete-terraform-role-non-mgmt - Deletes terraform role in the current non-mgmt account"
    echo
}

function _bootstrap() {
  command=$1
  env=$2
  args=(${@:3})

  case $command in
    "create-mgmt-state")
    if [[ "$(aws sts get-caller-identity)" != *mgmt* ]];
    then
        echo "Please log in as the mgmt account" >&2
        return 1
    fi

    cd $root/terraform/bootstrap/mgmt
    project_name=$(_get_project_name) || return 1
    region_name=$(_get_region_name) || return 1
    state_bucket_name=${project_name}-terraform-state
    aws s3api create-bucket --bucket ${state_bucket_name} --region us-east-1 --create-bucket-configuration LocationConstraint=${region_name}
    aws dynamodb create-table --cli-input-json file://locktable.json --region ${region_name}

    terraform init -upgrade || return 1
    terraform workspace select mgmt || terraform workspace new mgmt || return 1
    terraform init || return 1

    local profile_name=${PROFILE_PREFIX}-mgmt-admin
    local aws_account_id=$(_get_aws_info "$profile_name" aws_account_id) || return 1
    local role_name=$(_get_aws_info "$profile_name" role_name) || return 1

    terraform import \
        -var "assume_account=${aws_account_id}"  \
        -var "assume_role=${role_name}" \
        aws_dynamodb_table.dynamodb_terraform_state_lock \
        ${state_bucket_name}-lock || return 1

    terraform import \
        -var "assume_account=${aws_account_id}"\
        -var "assume_role=${role_name}"\
        aws_s3_bucket.terraform_state_bucket\
        ${state_bucket_name} || return 1

    terraform plan -var-file=etc/mgmt.tfvars -out=./tfplan -var "assume_account=${aws_account_id}" -var "assume_role=${role_name}" || return 1
    terraform apply ./tfplan || return 1
    ;;
    #----------------
    "delete-mgmt-state")
    if [[ "$(aws sts get-caller-identity)" != *mgmt* ]];
    then
        echo "Please log in as the mgmt account" >&2
        return 1
    fi

    cd $root/terraform/bootstrap/mgmt
    project_name=$(_get_project_name) || return 1
    state_bucket_name=${project_name}--terraform-state
    state_lock_name=${state_bucket_name}-lock

    aws dynamodb delete-table --table-name ${state_lock_name} || return 1

    versioned_objects=$(aws s3api list-object-versions \
                        --bucket "${state_bucket_name}" \
                        --output=json \
                        --query='{Objects: Versions[].{Key:Key,VersionId:VersionId}}') || return 1
    aws s3api delete-objects \
        --bucket ${state_bucket_name} \
        --delete ${versioned_objects} || echo "Ignore the previous warning - an empty bucket is a good thing"
    echo "Waiting for bucket contents to be deleted..." && sleep 10
    aws s3 rb s3://${state_bucket_name} || echo "Bucket could not be deleted at this time. You should go to the AWS Console and delete the bucket manually."
    ;;
    #----------------
    "create-terraform-role-non-mgmt")
    if [[ "$(aws sts get-caller-identity)" == *mgmt* ]];
    then
        echo "Please log in as a non-mgmt account" >&2
        return 1
    fi

    cd $root/terraform/bootstrap/non-mgmt
    local json_data=$(awk "{sub(/REPLACEME/,\"$(_get_mgmt_account)\")}1" terraform-trust-policy.json)
    aws iam create-role --role-name ${TERRAFORM_ROLE_NAME} --assume-role-policy-document ${json_data} || return 1
    aws iam attach-role-policy --policy-arn ${ADMIN_POLICY_ARN} --role-name ${TERRAFORM_ROLE_NAME} || return 1
    ;;
    #----------------
    "delete-terraform-role-non-mgmt")
    if [[ "$(aws sts get-caller-identity)" == *mgmt* ]];
    then
        echo "Please log in as a non-mgmt account" >&2
        return 1
    fi

    aws iam detach-role-policy --policy-arn ${ADMIN_POLICY_ARN} --role-name ${TERRAFORM_ROLE_NAME} || return 1
    aws iam delete-role --role-name ${TERRAFORM_ROLE_NAME} || return 1
    echo "Deleted role ${TERRAFORM_ROLE_NAME} and associated policy ${ADMIN_POLICY_ARN}"
    ;;
    #----------------
    *) _bootstrap_help $args ;;
    esac
}
