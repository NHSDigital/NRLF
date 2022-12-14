import json
import urllib.parse
from abc import abstractmethod
from dataclasses import dataclass, field
from types import FunctionType

import requests
from behave.model import Table
from lambda_pipeline.types import LambdaContext
from lambda_utils.header_config import AuthHeader, ClientRpDetailsHeader
from lambda_utils.tests.unit.utils import make_aws_event
from nrlf.producer.fhir.r4.model import OperationOutcome
from pydantic import BaseModel

from feature_tests.common.constants import (
    ALLOWED_APP_IDS,
    DEFAULT_AUTHORIZATION,
    DEFAULT_CLIENT_RP_DETAILS,
    DEFAULT_METHOD_ARN,
    STATUS_CODE_200,
    Action,
    ActorType,
    TestMode,
)
from feature_tests.common.utils import (
    get_action,
    get_actor,
    get_actor_type,
    get_org_id,
    logging_headers,
    render_regular_properties,
    render_relatesTo_properties,
)
from helpers.seed_data_repository import SeedDataRepository


@dataclass
class Template:
    raw: str

    def render(self, table: Table) -> str:
        return render_regular_properties(raw=self.raw, table=table)

    def render_fhir(self, table: Table) -> str:
        rendered = render_regular_properties(raw=self.raw, table=table)
        return render_relatesTo_properties(fhir_json=json.loads(rendered), table=table)


@dataclass
class Response:
    body: str
    status_code: str = STATUS_CODE_200

    def success(self):
        return self.status_code == STATUS_CODE_200

    @property
    def error(self) -> str:
        operation_outcome = OperationOutcome.parse_raw(self.body)
        (issue,) = operation_outcome.issue
        return issue.diagnostics

    @property
    def dict(self) -> dict:
        return json.loads(self.body)


@dataclass
class BaseRequest:
    endpoint: str = None
    headers: dict = field(default_factory=dict)
    client_rp_details: ClientRpDetailsHeader = field(
        default_factory=lambda: ClientRpDetailsHeader(**DEFAULT_CLIENT_RP_DETAILS)
    )
    scenario_name: str = None
    version: float = None
    sent_documents: list[str] = field(default_factory=list)
    sent_requests: list[str] = field(default_factory=list)

    @abstractmethod
    def _invoke(self, **kwargs) -> dict:
        raise NotImplementedError

    def invoke(self, **kwargs) -> Response:
        client_rp_details = {
            "NHSD-Client-RP-Details": self.client_rp_details.json(by_alias=True)
        }
        self.headers["Accept"] = f"version={self.version}"
        self.headers["Authorization"] = DEFAULT_AUTHORIZATION
        self.headers.update(**logging_headers(self.scenario_name))
        self.headers.update(**client_rp_details)
        raw_response = self._invoke(**kwargs)
        if kwargs.get("body"):
            self.sent_documents.append(kwargs["body"])
        return Response(**raw_response)

    def set_auth_headers(self, org_id: str, app_id: str, app_name: str):
        if app_id not in ALLOWED_APP_IDS:
            raise ValueError(f"App ID {app_id} must be one of {ALLOWED_APP_IDS}")

        auth_header = AuthHeader(**{"Organisation-Code": org_id}).dict(by_alias=True)
        self.client_rp_details.developer_app_id = app_id
        self.client_rp_details.developer_app_name = app_name
        self.headers.update(**auth_header)


@dataclass
class ApiRequest(BaseRequest):
    request_method: str = None
    method_slug: str = None

    def _invoke(
        self, body: str = None, query_params: dict = {}, path_params: dict = {}
    ) -> dict:
        url = f"{self.endpoint}{self.method_slug}"
        request_kwargs = {
            "method": self.request_method.upper(),
            "headers": self.headers,
        }
        if body:
            request_kwargs["data"] = body
        if query_params:
            request_kwargs["params"] = query_params
        for key, value in path_params.items():
            url = url.format(**{key: f"{urllib.parse.quote(value)}"})

        request_kwargs["url"] = url
        raw_response: requests.Response = requests.request(**request_kwargs)
        self.sent_requests.append(request_kwargs)
        return {"body": raw_response.text, "status_code": raw_response.status_code}


@dataclass
class LocalApiRequest(BaseRequest):
    handler: FunctionType = None

    def _invoke(self, body: dict = None, **kwargs) -> dict:
        authorizer = {"pointer_types": json.dumps(self.headers.pop("pointer-types"))}
        event = make_aws_event(
            body=body, headers=self.headers, authorizer=authorizer, **kwargs
        )
        response = self.handler(event=event, context=LambdaContext())
        return {"body": response["body"], "status_code": response["statusCode"]}


@dataclass
class AuthLambdaRequest(BaseRequest):
    lambda_client: any = None

    def _invoke(self) -> dict:
        event = make_aws_event(
            headers=self.headers, methodArn={"methodArn": DEFAULT_METHOD_ARN}
        )
        event.pop("isBase64Encoded")
        aws_response = self.lambda_client.invoke(
            FunctionName=self.endpoint,
            InvocationType="RequestResponse",
            Payload=json.dumps(event),
        )
        response = aws_response["Payload"].read().decode()
        return {"body": response, "status_code": None}


@dataclass
class LocalAuthLambdaRequest(BaseRequest):
    handler: FunctionType = None

    def _invoke(self) -> dict:
        event = make_aws_event(
            headers=self.headers, methodArn={"methodArn": DEFAULT_METHOD_ARN}
        )
        event.pop("isBase64Encoded")
        response = self.handler(event=event, context=LambdaContext())
        return {"body": json.dumps(response), "status_code": None}


@dataclass(init=False)
class ActorContext:
    actor: str
    actor_type: ActorType
    action: Action
    org_id: str

    def __init__(self, actor: str, actor_type: str, action: Action, org_id: str):
        self.action = get_action(action_name=action)
        self.actor_type = get_actor_type(actor_type_name=actor_type)
        self.actor = get_actor(actor=actor, actor_type=self.actor_type)
        self.org_id = get_org_id(org_id=org_id, actor_type=self.actor_type)


@dataclass
class TestConfig:
    mode: TestMode
    request: BaseRequest = field(default_factory=BaseRequest)
    response: Response = None
    repositories: dict[BaseModel, SeedDataRepository] = field(default_factory=dict)
    templates: dict[str, Template] = field(default_factory=dict)
    actor_context: ActorContext = None
