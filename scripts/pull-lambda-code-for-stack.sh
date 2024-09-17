#!/bin/bash
# Pull down all the lambda code for the named stack
set -o errexit -o nounset -o pipefail

: ${DIST_DIR:="./dist"}

stack_name="$1"

function pull_lambda_code(){
    local api_name="$1"
    local endpoint_name="$2"
    local lambda_name="nhsd-nrlf--${stack_name}--api--${api_name}--${endpoint_name}"

    echo -n "- Downloading code for lambda ${lambda_name}.... "
    code_url="$(aws lambda get-function  --function-name ${lambda_name} | jq -r .Code.Location)"
    curl "${code_url}" 2>/dev/null > "${DIST_DIR}/${api_name}-${endpoint_name}.zip"
    echo "✅"
}

function pull_layer_code(){
    local name="$1"
    local layer_name="nhsd-nrlf--${stack_name}--${name}"
    local layer_version="$(aws lambda list-layer-versions --layer-name ${layer_name} | jq -r '.LayerVersions[0].Version')"
    local layer_pkg_name="$(echo ${name} | tr '-' '_').zip"

    echo -n "- Downloading code for layer ${layer_name} version ${layer_version}...."
    code_url="$(aws lambda get-layer-version --layer-name ${layer_name} --version-number ${layer_version} | jq -r .Content.Location)"
    curl "${code_url}" 2>/dev/null > "${DIST_DIR}/${layer_pkg_name}"
    echo "✅"
}

mkdir -p "${DIST_DIR}"

echo
echo "Pulling code for consumer API lambdas...."
for endpoint_name in $(ls api/consumer)
do
    if [ ! -d "api/consumer/${endpoint_name}" ]; then
        continue
    fi

    pull_lambda_code "consumer" "${endpoint_name}"
done

echo
echo "Pulling code for producer API lambdas...."
for endpoint_name in $(ls api/producer)
do
    if [ ! -d "api/producer/${endpoint_name}" ]; then
        continue
    fi

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
