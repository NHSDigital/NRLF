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
    "check") python -m black . --check ;;
    "fix") python -m black . ;;
    *) _lint_help ;;
  esac
}
