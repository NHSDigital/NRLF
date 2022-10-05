#!/bin/bash

function _bootstrap_help() {
    echo
    echo "nrlf bootstrap <command> [options]"
    echo
    echo "commands:"
    echo "  help          - this help screen"
    echo "  create-mgmt-state - Creates terraform state files in the mgmt account"
    echo "  create-terraform-role-non-mgmt - Creates terraform role in the current non-mgmt account"
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
    project_name=$(_get_project_name)
    region_name=$(_get_region_name)
    state_bucket_name=${project_name}--terraform-state
    aws s3api create-bucket --bucket ${state_bucket_name} --region us-east-1 --create-bucket-configuration LocationConstraint=${region_name}
    aws dynamodb create-table --cli-input-json file://locktable.json --region ${region_name}

    terraform init -upgrade
    terraform workspace select mgmt || terraform workspace new mgmt
    terraform init

    local profile_name=${PROFILE_PREFIX}-mgmt-admin
    local aws_account_id=$(_get_aws_info "$profile_name" aws_account_id)
    local role_name=$(_get_aws_info "$profile_name" role_name)

    terraform import \
        -var "assume_account=${aws_account_id}"  \
        -var "assume_role=${role_name}" \
        aws_dynamodb_table.dynamodb_terraform_state_lock \
        ${state_bucket_name}-lock

    terraform import \
        -var "assume_account=${aws_account_id}"\
        -var "assume_role=${role_name}"\
        aws_s3_bucket.terraform_state_bucket\
        ${state_bucket_name}

    terraform plan -var-file=etc/mgmt.tfvars -out=./tfplan -var "assume_account=${aws_account_id}" -var "assume_role=${role_name}"
    terraform apply ./tfplan
    ;;

    "create-terraform-role-non-mgmt")
    if [[ "$(aws sts get-caller-identity)" == *mgmt* ]];
    then
        echo "Please log in as a non-mgmt account" >&2
        return 1
    fi

    cd $root/terraform/bootstrap/non-mgmt
    local json_data=$(awk "{sub(/REPLACEME/,\"$(_get_mgmt_account)\")}1" terraform-trust-policy.json)
    aws iam create-role --role-name terraform --assume-role-policy-document ${json_data}
    aws iam attach-role-policy --policy-arn arn:aws:iam::aws:policy/AdministratorAccess --role-name terraform
    ;;

    *) _bootstrap_help $args ;;
    esac
}