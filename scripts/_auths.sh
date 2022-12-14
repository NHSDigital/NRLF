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

    allowed_actor_types="producer consumer"
    if [[ " ${allowed_actor_types[*]} " =~ " ${actor_type} " ]]; then
        python3 auth_setup.py $actor_type $env
    else
        _auths_help
    fi
}
