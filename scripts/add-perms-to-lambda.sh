#!/bin/bash
# Add s3 perms to permissions layer
#
set -o errexit -o pipefail -o nounset

dist_path="$(pwd)/$1"

zip -q -r "${dist_path}/nrlf_permissions.zip" . && rm -rf "${dist_path}/nrlf_permissions"

echo "✅ New Layer Zip Created with S3 Permissions: ${dist_path}/nrlf_permissions.zip"
