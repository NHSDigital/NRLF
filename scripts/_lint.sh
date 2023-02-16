#!/bin/bash

function _lint_help() {
  echo
  echo "nrlf lint <command> [options]"
  echo
  echo "commands:"
  echo "  help          - this help screen"
  echo "  check         - check code linting"
  echo "  fix           - fix code linting"
  echo
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
  cd $root/terraform/account-wide-infrastructure/dev
  terraform fmt -check -recursive
  cd $root/terraform/account-wide-infrastructure/mgmt
  terraform fmt -check -recursive
  cd $root/terraform/account-wide-infrastructure/test
  terraform fmt -check -recursive
  cd $root/terraform/account-wide-infrastructure/prod
  terraform fmt -check -recursive
}

function _fix_lint() {
  python -m black .
  cd $root/terraform/infrastructure
  terraform fmt -recursive
  cd $root/terraform/account-wide-infrastructure/dev
  terraform fmt -recursive
  cd $root/terraform/account-wide-infrastructure/mgmt
  terraform fmt -recursive
  cd $root/terraform/account-wide-infrastructure/test
  terraform fmt -recursive
  cd $root/terraform/account-wide-infrastructure/prod
  terraform fmt -recursive
}
