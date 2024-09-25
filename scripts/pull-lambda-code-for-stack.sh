#!/bin/bash
# Pull down all the lambda code for the named stack
set -o errexit -o nounset -o pipefail

: "${DIST_DIR:="./dist"}"

if [ $# -ne 1 ]
then
    echo "Error: stack-name argument is missing" 1>&2
    echo "Usage: $0 <stack-name>" 1>&2
    exit 1
fi

stack_name="$1"

function pull_lambda_code(){
    local api_name="$1"
    local endpoint_name="$2"

    lambda_name="nhsd-nrlf--${stack_name}--api--${api_name}--${endpoint_name}"

    echo -n "- Downloading code for lambda ${lambda_name}.... "
    code_url="$(aws lambda get-function  --function-name "${lambda_name}" | jq -r .Code.Location)"
    curl "${code_url}" 2>/dev/null > "${DIST_DIR}/${api_name}-${endpoint_name}.zip"
    echo "✅"
}

function pull_layer_code(){
    local name="$1"

    layer_name="nhsd-nrlf--${stack_name}--${name}"
    layer_pkg_name="$(echo "${name}" | tr '-' '_').zip"
    layer_version="$(aws lambda list-layer-versions --layer-name "${layer_name}" | jq -r '.LayerVersions[0].Version')"

    echo -n "- Downloading code for layer ${layer_name} version ${layer_version}.... "
    code_url="$(aws lambda get-layer-version --layer-name "${layer_name}" --version-number "${layer_version}" | jq -r .Content.Location)"
    curl "${code_url}" 2>/dev/null > "${DIST_DIR}/${layer_pkg_name}"
    echo "✅"
}

mkdir -p "${DIST_DIR}"

echo
echo "Pulling code for consumer API lambdas...."
for endpoint_path in api/consumer/*
do
    if [ ! -d "${endpoint_path}" ]
    then
        continue
    fi

    endpoint_name="$(basename "${endpoint_path}")"
    pull_lambda_code "consumer" "${endpoint_name}"
done

echo
echo "Pulling code for producer API lambdas...."
for endpoint_path in api/producer/*
do
    if [ ! -d "${endpoint_path}" ]
    then
        continue
    fi

    endpoint_name="$(basename "${endpoint_path}")"
    pull_lambda_code "producer" "${endpoint_name}"
done

echo
echo "Pulling code for layers...."
for layer_name in nrlf dependency-layer nrlf-permissions
do
    pull_layer_code "${layer_name}"
done

echo
echo "✅ Done. Code is in ${DIST_DIR}"
echo
