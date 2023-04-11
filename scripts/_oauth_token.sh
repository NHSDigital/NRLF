#!/bin/bash

function _oauth_token() {
  local args=(${@:1})
  python api/tests/test_smoke.py token $args
}
