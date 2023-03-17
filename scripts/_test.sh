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
  "firehose") _test_integration_firehose $args ;;
  *) _test_help ;;
  esac
}

function _test_unit() {
  local args=(${@:1})
  python -m pytest -m "not integration and not legacy and not smoke" $args
}

function _test_integration() {
  local args=(${@:1})
  python -m pytest -m "integration and not firehose" $args
}

function _test_integration_firehose() {
  local args=(${@:1})
  python -m pytest -m "integration and firehose" --runslow $args
}

function _test_smoke() {
  local args=(${@:1})
  python -m pytest -m "smoke" $args
}

function _test_feature() {
  local command=$1
  local args=(${@:2})
  if [ -z $args ]; then
    args="./feature_tests"
  fi

  case $command in
  "local") python -m behave $args ;;
  "integration") python -m behave --define="integration_test=true" $args ;;
  *) _test_help ;;
  esac
}
