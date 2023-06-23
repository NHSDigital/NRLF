#!/bin/bash


function _firehose_help() {
    echo
    echo "nrlf firehose <command> [options]"
    echo
    echo "commands:"
    echo "  help                        - this help screen"
    echo "  fetch <s3_uri> <env>        - fetch and parse firehose logs from S3"
    echo "  validate <file_path>        - validate firehose logs"
    echo "  resubmit <file_path> <env>  - fetch and parse firehose logs from S3"
    echo
    return 1
}

function _firehose() {
    local verb=$1
    case $verb in
        "fetch") _firehose_fetch $2 $3 ;;
        "validate") _firehose_validate $2 $3 ;;
        "resubmit") _firehose_resubmit $2 $3 ;;
        *) _firehose_help ;;
    esac
}

function _firehose_fetch() {
    local bucket=$1
    local key=$2
    local env=$3
    python helpers/helpers/firehose.py fetch $1 $2 $3
}

function _firehose_validate() {
    local file_path=$1
    python helpers/helpers/firehose.py validate $1
}

function _firehose_resubmit() {
    local file_path=$1
    local env=$2
    python helpers/helpers/firehose.py resubmit $1 $2
}
