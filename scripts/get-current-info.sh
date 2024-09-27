#!/bin/bash
# Get the current info about the codebase
set -o errexit -o nounset -o pipefail

BRANCH_NAME="$(git rev-parse --abbrev-ref HEAD)"
TAG_NAME="$(git describe --tags || echo "no-tags")"
SHORT_COMMIT_HASH="$(git rev-parse --short=8 HEAD)"

if [ "${BRANCH_NAME}" == "HEAD" ]; then
    NRLF_VERSION="${TAG_NAME}@${SHORT_COMMIT_HASH}"
else
    NRLF_VERSION="${BRANCH_NAME}@${SHORT_COMMIT_HASH}"
fi

cat << EOF
{
    "version": "${NRLF_VERSION}",
    "tag": "${TAG_NAME}",
    "branch": "${BRANCH_NAME}",
    "commit": "${SHORT_COMMIT_HASH}"
}
EOF
