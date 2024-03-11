#!/bin/bash
# Check that the build environment is set up correctly, and warn about issues
#
set -o errexit -o pipefail -o nounset

: "${SHOULD_WARN_ONLY:="false"}"

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
echo "Checking build environment...."

BUILD_DEPENDENCIES="
    allure
    behave
    jq
    poetry
    pre-commit
    pytest
    python
    terraform
    tfenv
    yq
    zip
"

for dep in ${BUILD_DEPENDENCIES}; do
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

if [ "${POETRY_ACTIVE:=0}" != "1" ];
then
    warning "Poetry is not active. Run 'poetry shell' to activate it."
else
    success "Poetry is active"
fi
