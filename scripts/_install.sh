#!/bin/bash

function _install() {
    # Check for Python 3
    if ! command -v python3 &>/dev/null; then
        echo "Python 3 is not installed. Please install it before proceeding."
        exit 1
    fi

    # Check for pip
    if command -v pip3 &>/dev/null; then
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
        pip3 install pipx
    fi

    # Check for poetry
    if command -v poetry &>/dev/null; then
        echo "poetry is installed."
    else
        echo "poetry is not installed. Installing poetry..."
        pipx install poetry
    fi
}
