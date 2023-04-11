#!/bin/bash

function _make_help() {
  echo
  echo "nrlf make <command> [options]"
  echo
  echo "commands:"
  echo "  help          - this help screen"
  echo "  build         - Builds the code"
  echo "  clean         - Cleans the artefacts"
  echo "  install       - Setup local dependencies"
  echo
  return 1
}

function _make() {
  command=$1
  case $command in
  "build") _build ;;
  "clean") _clean ;;
  "install") _install ;;
  *) _make_help ;;
  esac
}

function _build() {
  find $root -name make.sh | xargs -I % bash -c 'cd "$(dirname %)" && ./make.sh build'
}

function _clean() {
  find $root -name make.sh | xargs -I % bash -c 'cd "$(dirname %)" && ./make.sh clean'
}

function _install() {
  # Check for Python 3
  if ! command -v python3 &>/dev/null; then
    echo "Python 3 is not installed. Please install it before proceeding."
    exit 1
  fi

  # Check for pip
  if command -v pip &>/dev/null; then
    echo "pip is installed."
  else
    echo "pip is not installed. Installing pip..."
    python3 -m ensurepip
  fi

  # Check for pipx
  if command -v pipx &>/dev/null; then
    echo "pipx is installed."
  else
    echo "pipx is not installed. Installing pipx..."
    python3 -m ensurepip
    python3 -m pip install pipx
  fi

  # Check for poetry
  if command -v poetry &>/dev/null; then
    echo "poetry is installed."
  else
    echo "poetry is not installed. Installing poetry..."
    pipx install poetry
  fi

}
