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
  echo "  firehose            - run firehose integration tests"
  echo
  return 1
}

function _test() {
  local command=$1
  local args=(${@:2})

  case $command in
  "unit") _test_unit $args ;;
  "integration") _test_integration $args ;;
  "integration_report") _test_integration_report $args ;;
  "smoke") python api/tests/test_smoke.py manual_smoke_test --actor $2 --environment $3 $4 ;;
  "token") _test_token $args ;;
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

function _test_integration_report() {
  local args=(${@:1})
  python -m pytest -m "integration and not firehose" $args --alluredir=./allure-results
}

function _test_integration_firehose() {
  local args=(${@:1})
  python -m pytest -m "integration and firehose" --runslow $args
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
  "integration_report")
      #The commented out line below can be uncommented if you wish to have a clean of the test results each run
      #rm -rf ./allure-results
      python -m behave --define="integration_test=true" $args
      allure generate ./allure-results -o ./allure-report --clean
      allure open ./allure-report ;;
  *) _test_help ;;
  esac
}
