#!/bin/bash

function _lint() {
  pre-commit run --all-files
}
