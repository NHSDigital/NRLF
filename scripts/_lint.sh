#!/bin/bash

function _lint_help() {
  echo
  echo "nrlf lint <command> [options]"
  echo
  echo "commands:"
  echo "  help          - this help screen"
  echo "  check         - check code linting"
  echo "  fix           - fix code linting"
  return 1
}

function _lint() {
  command=$1
  case $command in
    "check") _check_lint ;;
    "fix") _fix_lint ;;
    *) _lint_help ;;
  esac
}

function _check_lint() {
  python -m black . --check
  cd $root/terraform/infrastructure
  terraform fmt -check -recursive
}

function _fix_lint() {
  python -m black .
  cd $root/terraform/infrastructure
  terraform fmt -recursive
}
