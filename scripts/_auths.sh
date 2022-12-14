#!/bin/bash

function _auths_help() {
    echo
    echo "nrlf auths <actor_type> <env>"
    echo
    return 1
}

function _auths() {
    local env
    local actor_type=$1
    env=$(_get_environment_name "$2")
    cd scripts

    case $actor_type in
    "producer")
        python3 auth_setup.py $actor_type $env
        ;;
    "consumer")
        python3 auth_setup.py $actor_type $env
        ;;
    *)
        _auths_help
        ;;
    esac
}

function _get_environment_name() {
    local environment=$1

    if [[ -z $environment ]]; then
        if [[ -z $TERRAFORM_LOCAL_WORKSPACE_OVERRIDE ]]; then
            echo "$(whoami | openssl dgst -sha1 -binary | xxd -p | cut -c1-8)"
        else
            echo "$TERRAFORM_LOCAL_WORKSPACE_OVERRIDE"
        fi
    else
        echo "$environment"
    fi
}
