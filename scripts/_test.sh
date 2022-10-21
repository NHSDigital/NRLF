#!/bin/bash

function _test_help() {
    echo
    echo "nrlf test <command> [options]"
    echo
    echo "commands:"
    echo "  help                        - this help screen"
    echo "  unit                        - run unit tests"
    echo "  integration                 - run integration tests"
    echo "  feature                     - run BDD tests"
    echo
}

function _test() {
    local command=$1
    case $command in
        "unit") _test_unit "$2";;
        "integration") _test_integration ;;
        "feature") echo "not implemented" ;; #_test_feature ;;
        *) _test_help ;;
    esac
}

function _test_unit() {
    python -m pytest -m "not integration"
}


function _test_integration() {
    python -m pytest -m "integration"
}


function _test_feature() {
    python -m behave feature-tests
}
