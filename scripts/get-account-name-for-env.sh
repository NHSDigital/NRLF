#!/bin/bash
# Get the account name for the provided NRLF environment
set -o errexit -o nounset -o pipefail

if [ $# -ne 1 ]; then
    echo "Usage: get-account-name-for-env.sh <env>"
    exit 1
fi

env="$1"

case "${env}" in
    dev|dev-sandbox)
        echo "dev"
        ;;
    qa|qa-sandbox|ref|int|int-sandbox)
        echo "test"
        ;;
    prod)
        echo "prod"
        ;;
    *)
        echo "Unknown"
        exit 1
esac

exit 0
