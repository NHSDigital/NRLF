#!/bin/bash

export _HEALTHCHECK_ATTEMPTS=3
export _HEALTHCHECK_SLEEP_SECONDS=30
export _STATUSCHECK_ATTEMPTS=1
export _STATUSCHECK_SLEEP_SECONDS=60
export _STARTUP_TIME=10

function perform_healthcheck(){
    status_code=$(curl -s -o /dev/null -w "%{http_code}" ${1})
    if [ $status_code -eq 200 ];
    then
        return 0
    fi
    return 1
}

function healthcheck(){
    attempts=${3:-$_HEALTHCHECK_ATTEMPTS}
    for i in $(seq 1 $attempts);
    do
        perform_healthcheck ${2} && return 0
        echo "*** ${1} not ready, will retry in $_HEALTHCHECK_SLEEP_SECONDS seconds ***"
        sleep $_HEALTHCHECK_SLEEP_SECONDS
    done
    echo "ERROR: ${1} not alive after ${attempts} attempts"
    return 1
}

cd /opt/code/localstack/ && bash docker-entrypoint.sh &
sleep ${_STARTUP_TIME}
healthcheck "LocalStack" http://localhost:4566/health || exit 1
localstack_pid=$!

cd /code/proxy && poetry run python proxy.py &
sleep ${_STARTUP_TIME}
healthcheck "Proxy" http://localhost:8000/_status || exit 1

terraform_dir=/code/dist/terraform/infrastructure
poetry run bash -c "cd $terraform_dir && tflocal init" || exit 1
poetry run bash -c "cd $terraform_dir && tflocal apply -auto-approve -input=false  -var 'assume_account=000000000000' -var 'assume_role=sandbox'"|| exit 1
poetry run bash -c "cd $terraform_dir && tflocal output -json > /code/output.json" || exit 1
poetry remove terraform-local
rm -r /code/dist/

echo "All systems go"
while true; do
    healthcheck "LocalStack" http://localhost:4566/health $_STATUSCHECK_ATTEMPTS || exit 1
    healthcheck "Proxy" http://localhost:8000/_status $_STATUSCHECK_ATTEMPTS || exit 1
    sleep $_STATUSCHECK_SLEEP_SECONDS
done
