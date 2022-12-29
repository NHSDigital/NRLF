#!/bin/bash

function _oauth_token() {
  python api/tests/test_smoke.py --env=$1
}
