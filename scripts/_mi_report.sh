#!/bin/bash

function _mi_help() {
    echo
    echo "nrlf mi <command> [options]"
    echo
    echo "commands:"
    echo "  help                                       - this help screen"
    echo "  report <env> <?workspace> <?partition_key> - generate all reports for the given environment, workspace and partition key"
    echo "  seed-db <partition_key>                    - *for test purposes* seed test data into the database **in the active workspace**, using the provided partition key, which can then be used for testing reports"
    echo
    return 1
}

function _mi() {
    local verb=$1
    case $verb in
        "report") _mi_report $2 $3 $4 ;;
        "seed-db") _mi_seed_db $2 ;;
        *) _mi_help ;;
    esac
}

function _mi_report() {
    poetry run python -m mi.reporting.report $1 $2 $3
}

function _mi_seed_db() {
    poetry run python -m mi.reporting.tests.test_data.seed_database $1
}
