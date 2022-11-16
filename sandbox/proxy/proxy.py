import json
import os
import re
from functools import cache
from pathlib import Path

import requests
from flask import Flask, request

app = Flask(__name__)

LOCAL_STACK_URL = "http://localhost:4566"
STAGE_NAME = "production"
PATH_TO_TERRAFORM_OUTPUTS = Path(__file__).parent.parent / "output.json"
ID_FROM_URL_REGEX = re.compile("https://(\w+).*")
ERROR_404 = ("Not Found", 404)
ERROR_500 = ("Internal Server Error", 500)


def read_terraform_outputs():
    with open(PATH_TO_TERRAFORM_OUTPUTS) as f:
        return json.load(f)


def get_rest_api_metadata() -> list[dict]:
    terraform_outputs = read_terraform_outputs()
    return terraform_outputs["api_base_urls"]["value"]


@cache
def api_url(api_name: str, path: str) -> str:
    metadata = get_rest_api_metadata()
    (id,) = ID_FROM_URL_REGEX.search(metadata[api_name]).groups()
    return f"{LOCAL_STACK_URL}/restapis/{id}/{STAGE_NAME}/_user_request_/{path}"


@app.route("/_status", methods=["GET"])
def health() -> dict:
    try:
        response = requests.get(url=f"{LOCAL_STACK_URL}/health")
        response.raise_for_status()
    except Exception:
        return ERROR_500
    return {"message": "ok"}


@app.route("/<api_name>/<path:path>", methods=["GET", "POST", "PUT", "DELETE"])
def redirect_to_localstack(api_name: str, path: str) -> dict:
    try:
        localstack_url = api_url(api_name=api_name, path=path)
        headers = {
            k.lower(): v for k, v in dict(request.headers).items() if k != "HOST"
        }
        response = requests.request(
            url=localstack_url,
            headers=headers,
            method=request.method,
            data=request.get_data(),
            params=request.args.to_dict(),
        )
        if "Unable to find path" in response.text:
            return ERROR_404
    except Exception:
        return ERROR_500
    return response.text, response.status_code


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def catch_all(path: str):
    return ERROR_404


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=os.environ.get("DEBUG") == "1")
