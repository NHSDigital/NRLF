#!/bin/bash
# Build a lambda layer
#
set -o errexit -o pipefail -o nounset

layer_src_path="$1"
dist_path="$(pwd)/$2"

package_name="$(basename $layer_src_path)"

mkdir -p "${dist_path}/${package_name}-layer/python/${package_name}"
cp -r "${layer_src_path}"/* "${dist_path}/${package_name}-layer/python/${package_name}"

cd "${dist_path}/${package_name}-layer/" && \
    zip -q -r "${dist_path}/${package_name}.zip" . \
        -x **tests**\* **scripts**\* **__pycache__**\*

rm -rf "${dist_path}/${package_name}-layer"

echo "✅ Lambda Layer created: ${dist_path}/${package_name}.zip"
