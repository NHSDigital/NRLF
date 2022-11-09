#!/bin/bash

function _build() {
    python make.py
}

function _clean() {
    echo "Cleaning $(dirname "$(pwd)")"
    rm -rf ../dist
}

command=$1

case $command in
    "build") _build ;;
    "clean") _clean ;;
    *) echo "Unhandled command ${command}" ;;
esac
