#!/bin/bash

export root=$(cd $(dirname ${BASH_SOURCE[0]:-$0}) && pwd)

source $root/scripts/_constants.sh
source $root/scripts/_aws.sh
source $root/scripts/_bootstrap.sh
source $root/scripts/_terraform.sh
source $root/scripts/_make.sh

export file="${BASH_SOURCE##*/}"

function _show_help() {
    echo
    echo "nrlf <command> [options]"
    echo
    echo "This helper script calls terraform, enforcing some conventions:"
    echo "  1. work from root directory"
    echo "  2. include workspaces"
    echo "  3. force plan files"
    echo
    echo "commands:"
    echo "  help      - this help screen"
    echo "  make      - calls the make/build routines"
    echo "  aws       - aws commands"
    echo "  terraform - terraform commands"
    echo "  bootstrap - terraform commands"
    echo
}

function nrlf() {

  command=$1
  args=(${@:2})

  echo
  echo "Directory: $root"
  echo

  current=$(pwd)
  cd $root

  case $command in
    "aws") _aws $args ;;
    "make") _make $args ;;
    "terraform") _terraform $args ;;
    "bootstrap") _bootstrap $args ;;
    *) _show_help $args ;;
  esac

  cd $current
}

echo "Usage: nrlf"
