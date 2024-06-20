#!/bin/bash
# Add s3 perms to dependency layer
#
set -o errexit -o pipefail -o nounset

dist_path="$(pwd)/$1"

cd "${dist_path}" && zip -ur "${dist_path}/nrlf.zip" "python/nrlf/s3"

echo "✅ NRLF Layer Updated with S3 Permissions: ${dist_path}/nrlf.zip"
