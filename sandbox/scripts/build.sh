#!/bin/bash

sandbox_root=$PWD/../
repo_root=$sandbox_root/../

# Build docker container
cd $sandbox_root
docker-compose down &> /dev/null
docker-compose build && docker-compose up -d || return 1
CONTAINER_ID=$(docker-compose ps -q nrlf)

# Combine zip files
python $sandbox_root/scripts/sync_zips.py || return 1
python $sandbox_root/scripts/sync_terraform.py || return 1

# Build localstack infrastructure
sandbox_terraform_path=$sandbox_root/dist/terraform/infrastructure
cd $sandbox_terraform_path || return 1
poetry run tflocal init || return 1
poetry run tflocal apply -auto-approve -input=false  -var "assume_account=000000000000" -var "assume_role=sandbox"|| return 1
poetry run tflocal output -json > output.json || return 1
docker cp output.json $CONTAINER_ID:/code/output.json || return 1
cd $sandbox_root
