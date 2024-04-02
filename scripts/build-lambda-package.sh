#!/bin/bash
# Build a lambda package
#
set -o errexit -o pipefail -o nounset

api_src_path="$1"
dist_path="$(pwd)/$2"

api_type=$(basename $(dirname $api_src_path))
package_name="${api_type}-$(basename $api_src_path)"

cd "${api_src_path}" && \
    rm -f ${dist_path}/${package_name}.zip && \
    zip -q -r "${dist_path}/${package_name}.zip" . \
        -x tests**\* scripts**\* **__pycache__**\*

echo "✅ Package created: ${dist_path}/${package_name}.zip"
