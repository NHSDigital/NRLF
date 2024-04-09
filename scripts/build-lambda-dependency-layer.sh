#!/bin/bash
# Build a lambda layer
#
set -o errexit -o pipefail -o nounset

dist_path="$(pwd)/$1"

mkdir -p "${dist_path}/dependency_layer/python"

poetry export -f requirements.txt --without-hashes --output "${dist_path}/dependency_layer/requirements.txt"
pip install \
    --platform manylinux2014_x86_64 \
    --target="${dist_path}/dependency_layer/python" \
    --implementation cp \
    --python-version 3.12 \
    --only-binary=:all: --upgrade \
    -r "${dist_path}/dependency_layer/requirements.txt"

cd "${dist_path}/dependency_layer/" && \
    rm -f "${dist_path}/dependency_layer.zip" && \
    zip -q -r "${dist_path}/dependency_layer.zip" . \
        -x **tests**\* **scripts**\* **__pycache__**\*

rm -rf "${dist_path}/dependency_layer"

echo "✅ Dependency Layer created: ${dist_path}/dependency_layer.zip"
