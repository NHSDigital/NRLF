#!/bin/bash
# Add s3 perms to permissions layer
#
set -o errexit -o pipefail -o nounset

dist_path="$(pwd)/$1"

mkdir -p "${dist_path}/nrlf_permissions-layer/python/nrlf_permissions"
cp -r "${dist_path}/nrlf_permissions"/* "${dist_path}/nrlf_permissions-layer/python/nrlf_permissions"

cd "${dist_path}/nrlf_permissions-layer/" && \
    rm -f ${dist_path}/nrlf_permissions.zip && \
    zip -q -r "${dist_path}/nrlf_permissions.zip" . \
        -x **tests**\* **scripts**\* **__pycache__**\*

rm -rf "${dist_path}/nrlf_permissions-layer"
rm -rf "${dist_path}/nrlf_permissions"

echo "✅ New Layer Zip Created with S3 Permissions: ${dist_path}/nrlf_permissions.zip"
