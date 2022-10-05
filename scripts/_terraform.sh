#!/bin/bash


function _terraform_help() {
    echo
    echo "nrlf terraform <command> [options]"
    echo
    echo "commands:"
    echo "  help          - this help screen"
    echo "  validate      - runs 'terraform validate'"
    echo "  fmt           - runs 'terraform fmt'"
    echo "  init <env>    - runs 'terraform init'"
    echo "  plan <env>    - runs 'terraform plan'"
    echo "  apply <env>   - runs 'terraform apply'"
    echo "  destroy <env> - runs 'terraform destroy'"
    echo "  bootstrap-non-mgmt <env>   - Creates account-wide resources in the provided env"
    echo "  destroy-bootstrap-non-mgmt - Destroys account-wide resources in the provided env"
    echo
}

function _get_project_name(){
  python -c "import hcl; print(hcl.load(open('vars.tf'))['variable']['project_name']['default'])"
  return $?
}

function _get_region_name(){
  python -c "import hcl; print(hcl.load(open('vars.tf'))['variable']['region_name']['default'])"
  return $?
}

function _get_mgmt_account(){
  python -c "import os; from configparser import ConfigParser; parser = ConfigParser(); parser.read(os.environ['HOME'] + '/.aws/config'); print(parser['nhsd-nrlf-mgmt-admin']['aws_account_id'])"
  return $?
}

function _terraform() {
  command=$1
  env=$2
  args=(${@:3})

  case $command in
    #----------------
    "validate")
    cd $root/terraform
    terraform validate $args || return 1
    ;;
    #----------------
    "fmt")
    cd $root/terraform
    terraform fmt $args || return 1
    ;;
    #----------------
    "init")
    cd $root/terraform
    terraform workspace select $env || terraform workspace new $env || return 1
    terraform init $args || return 1
    ;;
    #----------------
    "plan")
    cd $root/terraform
    terraform workspace select $env || terraform workspace new $env || return 1
    terraform init || return 1
    terraform plan -var-file="./etc/${env}.tfvars" -out=./tfplan $args || return 1
    ;;
    #----------------
    "apply")
    cd $root/terraform
    terraform workspace select $env || terraform workspace new $env || return 1
    terraform init || return 1
    terraform apply $args ./tfplan || return 1
    ;;
    #----------------
    "destroy")
    cd $root/terraform
    terraform workspace select $env || terraform workspace new $env || return 1
    terraform init || return 1
    terraform destroy -var-file=./etc/dev.tfvars $args || return 1
    if [ $env != "default" ];
    then
      terraform workspace select default || return 1
      terraform workspace delete $env || return 1
    fi
    ;;
    #----------------
    "bootstrap-non-mgmt")
    if [[ "$(aws sts get-caller-identity)" != *mgmt* ]];
    then
        echo "Please log in as the mgmt account" >&2
        return 1
    fi

    if [[ -z ${env} ]];
    then
        echo "Non-mgmt parameter required" >&2
        echo "Usage:    nrlf terraform bootstrap-non-mgmt <ENV>"
        return 1
    fi

    local profile_name=${PROFILE_PREFIX}-$env-admin
    local aws_account_id=$(_get_aws_info "$profile_name" aws_account_id)

    cd $root/terraform/bootstrap/non-mgmt
    terraform init -upgrade || return 1
    terraform workspace select $env || terraform workspace new $env || return 1
    terraform init || return 1
    terraform plan -var-file=etc/non-mgmt.tfvars -out=./tfplan -var "assume_account=${aws_account_id}" || return 1
    terraform apply ./tfplan || return 1
    ;;
    #----------------
    "destroy-bootstrap-non-mgmt")
    if [[ "$(aws sts get-caller-identity)" != *mgmt* ]];
    then
        echo "Please log in as the mgmt account" >&2
        return 1
    fi

    if [[ -z ${env} ]];
    then
        echo "Non-mgmt parameter required" >&2
        echo "Usage:    nrlf terraform destroy-non-mgmt <ENV>"
        return 1
    fi

    local profile_name=${PROFILE_PREFIX}-$env-admin
    local aws_account_id=$(_get_aws_info "$profile_name" aws_account_id) || return 1

    cd $root/terraform/bootstrap/non-mgmt
    terraform workspace select $env || terraform workspace new $env || return 1
    terraform init || return 1
    terraform plan -destroy -var-file=etc/non-mgmt.tfvars -out=./tfplan -var "assume_account=${aws_account_id}" || return 1
    terraform apply -destroy ./tfplan || return 1
    if [ $env != "default" ];
    then
      terraform workspace select default || return 1
      terraform workspace delete $env || return 1
    fi
    ;;
    #----------------
    *) _terraform_help $args ;;
  esac
}