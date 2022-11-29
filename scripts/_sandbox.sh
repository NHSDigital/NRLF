#!/bin/bash


function _sandbox_help() {
    echo
    echo "nrlf sandbox <command> [options]"
    echo
    echo "commands:"
    echo "  help   - this help screen"
    echo "  build  - builds the sandbox image"
    echo "  up     - runs the sandbox locally"
    echo
    return 1
}


function _sandbox() {
  local command=$1
  sandbox_dir=$root/sandbox
  image_name=nrlf-sandbox:latest

  case $command in
    #----------------
    "build")
      cd $sandbox_dir || return 1
      python scripts/sync_zips.py || return 1
      python scripts/sync_terraform.py || return 1
      docker-compose down || return 1
      IMAGE_NAME=${image_name} docker-compose build || return 1
      cd $root
    ;;
    #----------------
    "up")
      cd $sandbox_dir || return 1
      docker-compose down || return 1
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
    *) _sandbox_help ;;
  esac
}
