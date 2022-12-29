#!/bin/bash

function _test_help() {
  echo
  echo "nrlf test <command> [options]"
  echo
  echo "commands:"
  echo "  help                - this help screen"
  echo "  unit                - run unit tests"
  echo "  integration         - run integration tests"
  echo "  smoke               - run smoke tests"
  echo "  feature local       - run local BDD tests"
  echo "  feature integration - run integration BDD tests"
  echo
  return 1
}

function _test() {
  local command=$1
  local args=(${@:2})

  case $command in
  "unit") _test_unit $args ;;
  "integration") _test_integration $args ;;
  "smoke") _test_smoke $args ;;
  "feature") _test_feature $args ;;
  *) _test_help ;;
  esac
}

function _test_unit() {
  local args=(${@:1})
  python -m pytest -m "not integration and not legacy and not smoke" $args
}

function _test_integration() {
  local args=(${@:1})
  python -m pytest -m "integration" $args
}

function _test_smoke() {
  local args=(${@:1})
  python -m pytest -m "smoke" $args
}

function _test_feature() {
  local command=$1

  case $command in
  "local") python -m behave feature_tests  ;;
  "integration") python -m behave --define="integration_test=true" feature_tests ;;
  *) _test_help ;;
  esac
}
