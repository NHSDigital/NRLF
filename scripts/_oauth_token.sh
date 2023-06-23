#!/bin/bash

function _oauth_token() {
  python helpers/helpers/oauth.py $1 $2
}
