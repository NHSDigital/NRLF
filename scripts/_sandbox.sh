#!/bin/bash


function _sandbox_help() {
    echo
    echo "nrlf sandbox <command> [options]"
    echo
    echo "commands:"
    echo "  help   - this help screen"
    echo "  build  - builds the sandbox image"
    echo "  up     - runs the sandbox locally"
    echo "  deploy - deploys the sandbox image to AWS"
    echo
    return 1
}


function _sandbox() {
  local command=$1
  sandbox_dir=$root/sandbox
  image_name=$(_get_image_name):latest

  case $command in
    #----------------
    "build")
      nrlf make clean
      nrlf make build
      cd $sandbox_dir || return 1
      python scripts/sync_zips.py || return 1
      python scripts/sync_terraform.py || return 1
      docker-compose down &> /dev/null || return 1
      IMAGE_NAME=${image_name} docker-compose build || return 1
      cd $root
    ;;
    #----------------
    "up")
      cd $sandbox_dir || return 1
      docker-compose down &> /dev/null || return 1
      IMAGE_NAME=${image_name} docker-compose up -d || return 1
      CONTAINER_ID=$(docker-compose ps -q nrlf)
      echo -n "Waiting for terraform to finish..."
      for i in $(seq 1 10);
      do
          docker logs --tail 100 $CONTAINER_ID 2>&1 | grep "All systems go" && break
          if [ $i -eq 10 ];
          then
            echo "ERROR: Could not verify terraform completion" && return 1
          fi
          sleep 20
          echo -n "."
      done
      cd $root
    ;;
    #----------------
    "deploy")
      cd $sandbox_dir || return 1
      docker-compose down &> /dev/null || return 1

      aws_account_id=$(_get_aws_account_id $2)
      repo_id=${aws_account_id}.dkr.ecr.${AWS_REGION_NAME}.amazonaws.com
      assume_role="arn:aws:iam::${aws_account_id}:role/${TERRAFORM_ROLE_NAME}"

      cd $root
      ecr_login_password=$(poetry run python -c "from helpers.ecr import get_ecr_password; print(get_ecr_password())")
      echo -n ${ecr_login_password} | docker login --username AWS --password-stdin ${repo_id} || return 1
      cd $sandbox_dir

      # Can be any role here
      docker tag ${image_name} ${repo_id}/${image_name} || return 1
      time docker push ${repo_id}/${image_name}
      if [ $? -gt 0 ];
      then
        echo "Deploy failed"
        return 1
      fi
      cd $root
      poetry run python -c "from helpers.ecs import refresh_ecs_service; refresh_ecs_service('sandbox_ecs_cluster')"
    ;;
    #----------------
    *) _sandbox_help ;;
  esac
}

function _get_image_name(){
  echo $(cat $root/terraform/infrastructure/output.json | jq -r .sandbox_image_name.value) || return 1
}
