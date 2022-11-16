#!/bin/bash
cd /code/proxy
curl -sSf http://0.0.0.0:8000/_status &> /dev/null || poetry run python proxy.py &

cd /opt/code/localstack/
curl -sSf http://0.0.0.0:4566/health &> /dev/null || bash docker-entrypoint.sh
