#!/bin/bash

function _test_help() {
  echo
  echo "nrlf test <command> [options]"
  echo
  echo "commands:"
  echo "  help                        - this help screen"
  echo "  unit                        - run unit tests"
  echo "  integration                 - run integration tests"
  echo "  feature local               - run local BDD tests"
  echo "  feature integration         - run integration BDD tests"
  echo
  return 1
}

function _test() {
  local command=$1
  case $command in
  "unit") _test_unit "$2" ;;
  "integration") _test_integration ;;
  "feature") _test_feature "$2" ;;
  *) _test_help ;;
  esac
}

function _test_unit() {
  python -m pytest -m "not integration" "$1"
}

function _test_integration() {
  python -m pytest -m "integration"
}

function _test_feature() {
  local command=$1

  case $command in
  "local") python -m behave feature_tests  ;;
  "integration") python -m behave --define="integration_test=true" feature_tests ;;
  *) _test_help ;;
  esac
}
