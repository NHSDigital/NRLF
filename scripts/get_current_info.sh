#!/bin/bash
# Get the current info about the codebase
set -o errexit -o nounset -o pipefail

BRANCH_NAME="$(git rev-parse --abbrev-ref HEAD)"
SHORT_COMMIT_HASH="$(git rev-parse --short=8 HEAD)"

echo "{ \"version\": \"${BRANCH_NAME}@${SHORT_COMMIT_HASH}\" }"
