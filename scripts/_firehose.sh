#!/bin/bash


function _firehose_help() {
    echo
    echo "nrlf firehose <command> [options]"
    echo
    echo "commands:"
    echo "  help                  - this help screen"
    echo "  fetch <bucket> <key>  - fetch and parse firehose logs from S3"
    echo
    return 1
}

function _firehose() {
    local verb=$1
    case $verb in
        "fetch") _firehose_fetch $2 $3 ;;
        *) _firehose_help ;;
    esac
}

function _firehose_fetch() {
    local bucket=$1
    local key=$2
    response=$(python -c "from helpers.firehose import fetch_logs_from_s3; import json; print(json.dumps(fetch_logs_from_s3(bucket_name='$bucket', file_key='$key')))")

    local outfile="$root/.firehose/$bucket/${key%.gz}.json"
    mkdir -p $(dirname $outfile)
    echo $response > $outfile
    echo "Downloaded $key to $outfile"
}
