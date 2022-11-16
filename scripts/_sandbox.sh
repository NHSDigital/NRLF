#!/bin/bash


function _sandbox_help() {
    echo
    echo "nrlf sandbox <command> [options]"
    echo
    echo "commands:"
    echo "  help  - this help screen"
    echo "  build - builds the sandbox and runs locally"
    echo
    return 1
}


function _sandbox() {
  local command=$1
  sandbox_dir=$root/sandbox

  case $command in
    #----------------
    "build")
      nrlf make build
      cd $sandbox_dir/scripts || return 1
      source build.sh || return 1
      cd $root
    ;;
    #----------------
    *) _sandbox_help ;;
  esac
}
