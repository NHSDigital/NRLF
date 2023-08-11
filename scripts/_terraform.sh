#!/bin/bash


function _terraform_help() {
    echo
    echo "nrlf terraform <command> [options]"
    echo
    echo "commands:"
    echo "  help                         - this help screen"
    echo "  validate <account_wide>      - runs 'terraform validate'"
    echo "  init <env> <account_wide>    - runs 'terraform init'"
    echo "  plan <env> <account_wide>    - runs 'terraform plan'"
    echo "  apply <env> <account_wide>   - runs 'terraform apply'"
    echo "  destroy <env> <account_wide> - runs 'terraform destroy'"
    echo
    return 1
}

function _terraform() {
  local command=$1
  local extra_command=$3
  local env
  local aws_account_id
  local var_file
  local current_timestamp
  local terraform_dir
  env=$(_get_environment_name "$2")
  aws_account_id=$(_get_aws_account_id "$env")
  var_file=$(_get_environment_vars_file "$env")
  terraform_dir=$(_get_terraform_dir "$env" "$extra_command")
  current_timestamp="$(date '+%Y_%m_%d__%H_%M_%S')"
  local plan_file="./tfplan"
  local ci_log_bucket="${PROFILE_PREFIX}--mgmt--github-ci-logging"

  case $command in
    "truststore") _terraform_truststore $env ;;
    #----------------
    "validate")
      cd "$terraform_dir" || return 1
      terraform validate || return 1
    ;;
    #----------------
    "init")
      if [[ "$(aws sts get-caller-identity)" != *mgmt* ]]; then
        echo "Please log in as the mgmt account" >&2
        return 1
      fi

      cd "$terraform_dir" || return 1
      _terraform_init "$env"
    ;;
    #----------------
    "plan")
      if [[ "$(aws sts get-caller-identity)" != *mgmt* ]]; then
        echo "Please log in as the mgmt account" >&2
        return 1
      fi

      cd "$terraform_dir" || return 1
      _terraform_plan "$env" "$var_file" "$plan_file" "$aws_account_id" "$extra_command"
    ;;
    #----------------
    "apply")
      if [[ "$(aws sts get-caller-identity)" != *mgmt* ]]; then
        echo "Please log in as the mgmt account" >&2
        return 1
      fi

      cd "$terraform_dir" || return 1
      _terraform_apply "$env" "$plan_file"
    ;;
    #----------------
    "destroy")
      if [[ "$(aws sts get-caller-identity)" != *mgmt* ]]; then
        echo "Please log in as the mgmt account" >&2
        return 1
      fi

      if [[ -z ${env} ]]; then
        echo "Non-mgmt parameter required" >&2
        echo "Usage:    nrlf terraform bootstrap-non-mgmt <ENV>"
        return 1
      fi

      cd "$terraform_dir" || return 1
      _terraform_destroy "$env" "$var_file" "$aws_account_id"
    ;;

    "ciinit")
      if [[ "$RUNNING_IN_CI" != 1 ]]; then
        echo "Command should only be used by CI pipeline" >&2
        return 1
      fi

      echo "Init terraform for aws workspace: ${env}"

      local tf_init_output="${env}-tf-init-output_${current_timestamp}.txt"

      cd "$terraform_dir" || return 1
      _terraform_init "$env" |& tee "./${tf_init_output}" > /dev/null
      local tf_init_status="${PIPESTATUS[0]}"
      aws s3 cp "./${tf_init_output}" "s3://${ci_log_bucket}/${env}/${tf_init_output}"

      echo "Init complete. Uploaded output to: s3://${ci_log_bucket}/${env}/${tf_init_output}"
      return "$tf_init_status"
    ;;

    "ciplan")
      if [[ "$RUNNING_IN_CI" != 1 ]]; then
        echo "Command should only be used by CI pipeline" >&2
        return 1
      fi

      echo "Creating plan for aws workspace: ${env}"

      local tf_plan_output="${env}-tf-plan-output_${current_timestamp}.txt"

      cd "$terraform_dir" || return 1
      _terraform_plan "$env" "$var_file" "$plan_file" "$aws_account_id" |& tee "./${tf_plan_output}" > /dev/null
      local tf_plan_status="${PIPESTATUS[0]}"
      aws s3 cp "./${tf_plan_output}" "s3://${ci_log_bucket}/${env}/${tf_plan_output}"

      echo "Plan complete. Uploaded output output to: s3://${ci_log_bucket}/${env}/${tf_plan_output}"
      return "$tf_plan_status"
    ;;

    "ciapply")

      if [[ "$RUNNING_IN_CI" != 1 ]]; then
        echo "Command should only be used by CI pipeline" >&2
        return 1
      fi

      echo "Applying change to aws workspace: ${env}"

      local tf_apply_output="${env}-tf-apply-output_${current_timestamp}.txt"

      cd "$terraform_dir" || return 1
      _terraform_apply "$env" "$plan_file" |& tee "./${tf_apply_output}" > /dev/null
      local tf_apply_status="${PIPESTATUS[0]}"
      aws s3 cp "./${tf_apply_output}" "s3://${ci_log_bucket}/${env}/${tf_apply_output}"

      echo "Apply complete. Uploaded output output to: s3://${ci_log_bucket}/${env}/${tf_apply_output}"
      return "$tf_apply_status"
    ;;

    "cidestroy")
      if [[ "$RUNNING_IN_CI" != 1 ]]; then
        echo "Command should only be used by CI pipeline" >&2
        return 1
      fi

      echo "Destroying aws workspace: ${env}"

      local tf_destroy_output="${env}-tf-destroy-output_${current_timestamp}.txt"

      cd "$terraform_dir" || return 1
      _terraform_destroy "$env" "$var_file" "$aws_account_id" "-auto-approve" |& tee "./${tf_destroy_output}" > /dev/null
      local tf_destroy_status="${PIPESTATUS[0]}"
      aws s3 cp "./${tf_destroy_output}" "s3://${ci_log_bucket}/${env}/${tf_destroy_output}"

      echo "Destroy complete. Uploaded output output to: s3://${ci_log_bucket}/${env}/${tf_destroy_output}"
      return "$tf_destroy_status"
    ;;
    #----------------
    *) _terraform_help ;;
  esac
}

function _get_environment_name() {
  local environment=$1

  if [[ -z $environment ]]; then
    if [[ -z $TERRAFORM_LOCAL_WORKSPACE_OVERRIDE ]]; then
      echo "$(whoami | openssl dgst -sha1 -binary | xxd -p | cut -c1-8)"
    else
      echo "$TERRAFORM_LOCAL_WORKSPACE_OVERRIDE"
    fi
  else
    echo "$environment"
  fi
}

function _get_account_id_location() {
  local environment=$1

  if [ "$RUNNING_IN_CI" = 1 ] && [ "$CI_DEPLOY_PERSISTENT_ENV" != 1 ]; then
    echo "${TEST_ACCOUNT_ID_LOCATION}"     # CI deployments to TEST by default
  elif [ "$environment" = "mgmt" ]; then
    echo "${MGMT_ACCOUNT_ID_LOCATION}"
  elif [ "$environment" = "prod" ]; then
    echo "${PROD_ACCOUNT_ID_LOCATION}"
  elif [ "$environment" = "ref" ] || [ "$environment" = "test" ] || [ "$environment" = "ref-sandbox" ]; then
    echo "${TEST_ACCOUNT_ID_LOCATION}"
  elif [ "$environment" = "int" ] || [ "$environment" = "uat" ] || [ "$environment" = "int-sandbox" ]; then
    echo "${TEST_ACCOUNT_ID_LOCATION}"
  else
    echo "${DEV_ACCOUNT_ID_LOCATION}"
  fi
}

function _get_aws_account_id() {
  local account_id_location
  account_id_location=$(_get_account_id_location "$1")
  aws secretsmanager get-secret-value --secret-id "$account_id_location" --query SecretString --output text
}

function _get_environment_vars_file() {
  local environment=$1
  local vars_prefix="dev"

  if [ "$RUNNING_IN_CI" = 1 ] && [ "$CI_DEPLOY_PERSISTENT_ENV" != 1 ]; then
    vars_prefix="test"
  elif [ "$environment" = "mgmt" ]; then
    vars_prefix="mgmt"
  elif [ "$environment" = "prod" ]; then
    vars_prefix="prod"
  elif [ "$environment" = "ref" ] || [ "$environment" = "test" ] || [ "$environment" = "ref-sandbox" ]; then
    vars_prefix="test"
  elif [ "$environment" = "int" ] || [ "$environment" = "uat" ] || [ "$environment" = "int-sandbox" ]; then
    vars_prefix="uat"
  fi

  echo "./etc/${vars_prefix}.tfvars"
}


function _terraform_init() {
  local env=$1
  local args=${@:2}

  terraform init $args || return 1
  terraform workspace select "$env" || terraform workspace new "$env" || return 1
}


function _terraform_plan() {
  local env=$1
  local var_file=$2
  local plan_file=$3
  local aws_account_id=$4
  local args=${@:5}

  terraform init || return 1
  terraform workspace select "$env" || terraform workspace new "$env" || return 1
  terraform plan \
    -out="$plan_file" \
    -var-file="$var_file" \
    -var "assume_account=${aws_account_id}" \
    -var "assume_role=${TERRAFORM_ROLE_NAME}" \
    $args || return 1
}


function _terraform_apply() {
  local env=$1
  local plan_file=$2
  local args=${@:4}

  terraform workspace select "$env" || terraform workspace new "$env" || return 1
  terraform apply $args "$plan_file" || return 1
  terraform output -json > output.json || return 1
}


function _terraform_destroy() {
  local env=$1
  local var_file=$2
  local aws_account_id=$3
  local args=${@:4}

  terraform workspace select "$env" || terraform workspace new "$env" || return 1
  terraform destroy \
    -var-file="$var_file" \
    -var "assume_account=${aws_account_id}" \
    -var "assume_role=${TERRAFORM_ROLE_NAME}" \
    $args || return 1
  if [ "$env" != "default" ]; then
    terraform workspace select default || return 1
    terraform workspace delete "$env" || return 1
  fi
}

function _get_terraform_dir() {
  local env=$1
  local account_wide=$2
  if [ "$RUNNING_IN_CI" = 1 ]; then
    echo "$root/terraform/infrastructure"
  elif [ "$account_wide" = "account_wide" ]; then
    echo "$root/terraform/account-wide-infrastructure/$env"
  else
    echo "$root/terraform/infrastructure"
  fi
}
