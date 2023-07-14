#!/bin/bash

export PIPENV_VENV_IN_PROJECT=1
root=$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)

for script_file in "$root"/scripts/*.sh; do
  source $script_file
done

function _nrlf_commands_help() {
  echo
  echo "nrlf <command> [options]"
  echo
  echo "commands:"
  echo "  help        - this help screen"
  echo "  aws         - aws commands"
  echo "  bootstrap   - bootstrap commands"
  echo "  lint        - lint commands"
  echo "  make        - calls the make/build routines"
  echo "  doc         - publish documentation into confluence"
  echo "  oauth <env> - Generates an oauth token for the env [dev, ref, prod]"
  echo "  swagger     - swagger generation commands"
  echo "  terraform   - terraform commands"
  echo "  test        - run tests"
  echo "  truststore  - manage the certificates for the API TLS MA"
  echo "  mi          - MI reporting tools"
  echo
  return 1
}

function nrlf() {
  if [ "$RUNNING_IN_CI" = "1" ]; then
    echo $0 $@
  fi

  local current=$(pwd)
  local command=$1

  cd $root

  case $command in
    "aws") _aws "${@:2}" ;;
    "make") _make "${@:2}" ;;
    "oauth") _oauth_token "${@:2}" ;;
    "terraform") _terraform "${@:2}" ;;
    "test") _test "${@:2}" ;;
    "bootstrap") _bootstrap "${@:2}" ;;
    "lint") _lint "${@:2}" ;;
    "swagger") _swagger "${@:2}" ;;
    "truststore") _truststore "${@:2}" ;;
    "doc") _doc "${@:2}" ;;
    "firehose") _firehose "${@:2}" ;;
    "mi") _mi "${@:2}" ;;
    *) _nrlf_commands_help ;;
  esac

  cd $current
}

echo "Usage: nrlf"
