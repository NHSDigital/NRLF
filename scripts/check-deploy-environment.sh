#!/bin/bash
# Check that the deployment environment is set up correctly, and warn about issues
#
set -o errexit -o pipefail -o nounset

: "${SHOULD_WARN_ONLY:="false"}"
: "${ENV:="dev"}"
: "${ENV_ACCOUNT_NAME:="dev"}"

function success() {
  [ "${SHOULD_WARN_ONLY}" == "true" ] && return

  local message="$1"
  echo "  ✅  ${message}"
}

function warning() {
  local message="$1"
  echo -e "  ⚠️  \e[31m${message}\e[39m"
}

echo
echo "Checking deployment environment...."

DEPLOY_DEPENDENCIES="
    aws
    terraform
"
for dep in ${DEPLOY_DEPENDENCIES}; do
    set +e
        dep_path="$(which ${dep} 2> /dev/null)"
    set -e

    if [ -n "${dep_path}" -a -x "${dep_path}" ]
    then
        success "${dep} found at ${dep_path}"
    else
        warning "${dep} not found ${dep_path}"
    fi
done

# Check the mgmt account has the environments account id
set +e
env_account_id="$(aws secretsmanager get-secret-value --secret-id nhsd-nrlf--mgmt--${ENV_ACCOUNT_NAME}-account-id --query SecretString --output text)"
set -e
if [ -n "${env_account_id}" ]
then
    success "${ENV_ACCOUNT_NAME} account id found in mgmt account"
else
    warning "${ENV_ACCOUNT_NAME} account id not found in mgmt account. Check you are logged into the NRLF mgmt account."
fi

# Check the Terraform workspace is set
set +e
tf_workspace="$(cd terraform/infrastructure && terraform workspace show)"
set -e
case "${tf_workspace}" in
    dev|qa|int|ref|prod)
        warning "Terraform workspace set to persistent environment '${tf_workspace}'"
        if [ "${tf_workspace}" != "${ENV}" ]
        then
            warning "Terraform workspace '${tf_workspace}' does not match deployment environment '${ENV}'"
        fi
        ;;
    dev-sandbox|qa-sandbox|int-sandbox)
        warning "Terraform workspace set to sandbox environment '${tf_workspace}'"
        ;;
    account_wide|default)
        warning "Terraform workspace set to '${tf_workspace}'"
        ;;
    *)
        success "Terraform workspace set to '${tf_workspace}'"
        ;;
esac
