import urllib.parse
from typing import Any

from aws_lambda_powertools.utilities.parser.models import APIGatewayProxyEventModel
from lambda_pipeline.types import FrozenDict, LambdaContext, PipelineData
from nrlf.core.errors import ItemNotFound
from pydantic import BaseModel, validator


class RaiseValidationErrorModel(BaseModel):
    foo: bool

    @validator("foo")
    def something(value):
        raise ValueError


class RaiseItemNotFoundErrorModel(BaseModel):
    foo: bool

    @validator("foo")
    def something(value):
        raise ItemNotFound


def throw_validation_error(
    data: PipelineData,
    context: LambdaContext,
    event: APIGatewayProxyEventModel,
    dependencies: FrozenDict[str, Any],
) -> PipelineData:
    RaiseValidationErrorModel(foo="1")


def throw_item_not_found_error(
    data: PipelineData,
    context: LambdaContext,
    event: APIGatewayProxyEventModel,
    dependencies: FrozenDict[str, Any],
) -> PipelineData:
    RaiseItemNotFoundErrorModel(foo="1")


def make_aws_event(authorizer={}, **kwargs):
    return {
        "resource": "/",
        "path": "/",
        "httpMethod": "GET",
        **kwargs.get("methodArn", {}),
        "headers": {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9;version="
            + kwargs.get("version", "1"),
            "accept-encoding": "gzip, deflate, br",
            "accept-language": "en-US,en;q=0.9",
            "cookie": "s_fid=7AAB6XMPLAFD9BBF-0643XMPL09956DE2; regStatus=pre-register",
            "Host": "70ixmpl4fl.execute-api.us-east-2.amazonaws.com",
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "none",
            "upgrade-insecure-requests": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.132 Safari/537.36",
            "X-Amzn-Trace-Id": "Root=1-5e66d96f-7491f09xmpl79d18acf3d050",
            "X-Forwarded-For": "52.255.255.12",
            "X-Forwarded-Port": "443",
            "X-Forwarded-Proto": "https",
            **kwargs.get("headers", {}),
        },
        "multiValueHeaders": {
            "accept": [
                "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9;version="
                + kwargs.get("version", "1")
            ],
            "accept-encoding": ["gzip, deflate, br"],
            "accept-language": ["en-US,en;q=0.9"],
            "cookie": [
                "s_fid=7AABXMPL1AFD9BBF-0643XMPL09956DE2; regStatus=pre-register;"
            ],
            "Host": ["70ixmpl4fl.execute-api.ca-central-1.amazonaws.com"],
            "sec-fetch-dest": ["document"],
            "sec-fetch-mode": ["navigate"],
            "sec-fetch-site": ["none"],
            "upgrade-insecure-requests": ["1"],
            "User-Agent": [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.132 Safari/537.36"
            ],
            "X-Amzn-Trace-Id": ["Root=1-5e66d96f-7491f09xmpl79d18acf3d050"],
            "X-Forwarded-For": ["52.255.255.12"],
            "X-Forwarded-Port": ["443"],
            "X-Forwarded-Proto": ["https"],
        },
        "queryStringParameters": kwargs.get("queryStringParameters"),
        "multiValueQueryStringParameters": None,
        "pathParameters": {
            k: urllib.parse.quote(v)
            for k, v in kwargs.get("pathParameters", {}).items()
        },
        "stageVariables": None,
        "requestContext": {
            "resourceId": "2gxmpl",
            "resourcePath": "/",
            "httpMethod": "GET",
            "extendedRequestId": "JJbxmplHYosFVYQ=",
            "requestTime": "10/Mar/2020:00:03:59 +0000",
            "path": "/Prod/",
            "accountId": "123456789012",
            "protocol": "HTTP/1.1",
            "stage": "Prod",
            "domainPrefix": "70ixmpl4fl",
            "requestTimeEpoch": 1583798639428,
            "requestId": "77375676-xmpl-4b79-853a-f982474efe18",
            "identity": {
                "cognitoIdentityPoolId": None,
                "accountId": None,
                "cognitoIdentityId": None,
                "caller": None,
                "sourceIp": "52.255.255.12",
                "principalOrgId": None,
                "accessKey": None,
                "cognitoAuthenticationType": None,
                "cognitoAuthenticationProvider": None,
                "userArn": None,
                "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.132 Safari/537.36",
                "user": None,
            },
            "domainName": "70ixmpl4fl.execute-api.us-east-2.amazonaws.com",
            "apiId": "70ixmpl4fl",
            "authorizer": authorizer,
        },
        "body": kwargs.get("body", None),
        "isBase64Encoded": False,
    }
