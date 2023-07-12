#!/bin/bash

branch=$(git symbolic-ref --short HEAD)
if [[ "${branch}" == *"release/"* ]]; then
    result=`python ./changelog/scripts/changelog.py $branch`
    if [[ "${result}" != "CHANGELOG.md updated." ]]; then
        echo "SUCCESS: CHANGELOG.md was out of date and has now been updated. Please re-commit."
        exit 1
    elif [[ "${result}" == "No matching changelog for release branch." ]]; then
        echo "FAILURE: You must create a change log to match the release branch."
        exit 1
    else
        exit 0
    fi
else
    exit 0
fi
