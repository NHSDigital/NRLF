import json
import urllib.parse
from abc import abstractmethod
from dataclasses import dataclass, field
from types import FunctionType

import requests
from behave.model import Table
from behave.runner import Context as BehaveContext
from lambda_pipeline.types import LambdaContext
from lambda_utils.header_config import ClientRpDetailsHeader, ConnectionMetadata
from lambda_utils.tests.unit.utils import make_aws_event
from pydantic import BaseModel

from feature_tests.common.constants import (
    AUTH_STORE,
    DEFAULT_AUTHORIZATION,
    DEFAULT_METHOD_ARN,
    STATUS_CODE_200,
    Action,
    ActorType,
    FhirType,
    TestMode,
)
from feature_tests.common.repository import FeatureTestRepository
from feature_tests.common.utils import (
    get_action,
    get_actor,
    get_actor_type,
    get_org_id,
    logging_headers,
    render_document_reference_properties,
    render_regular_properties,
)
from nrlf.core.authoriser import _parse_list_from_s3
from nrlf.core.constants import CLIENT_RP_DETAILS, CONNECTION_METADATA
from nrlf.core.types import DynamoDbClient, S3Client
from nrlf.core.validators import json_loads
from nrlf.producer.fhir.r4.model import OperationOutcome


@dataclass
class Template:
    raw: str

    def render(self, table: Table, fhir_type: FhirType = None) -> str:
        rendered = render_regular_properties(raw=self.raw, table=table)
        if fhir_type is FhirType.DocumentReference:
            return render_document_reference_properties(
                document_reference_json=json_loads(rendered), table=table
            )
        return rendered


@dataclass
class Response:
    body: str
    status_code: str = STATUS_CODE_200

    def success(self):
        return 300 > int(self.status_code) >= int(STATUS_CODE_200)

    @property
    def operation_outcome_msg(self) -> str:
        operation_outcome = OperationOutcome.parse_raw(self.body)
        (issue,) = operation_outcome.issue
        return issue.diagnostics

    @property
    def dict(self) -> dict:
        return json_loads(self.body)


@dataclass
class BaseRequest:
    endpoint: str = None
    headers: dict = field(default_factory=dict)
    scenario_name: str = None
    version: float = None
    sent_documents: list[str] = field(default_factory=list)
    sent_requests: list[str] = field(default_factory=list)

    @abstractmethod
    def _invoke(self, **kwargs) -> dict:
        raise NotImplementedError

    def invoke(self, **kwargs) -> Response:
        self.headers["Accept"] = f"version={self.version}"
        self.headers["Authorization"] = DEFAULT_AUTHORIZATION
        self.headers.update(**logging_headers(self.scenario_name))
        raw_response = self._invoke(**kwargs)
        if kwargs.get("body"):
            self.sent_documents.append(kwargs["body"])
        return Response(**raw_response)


@dataclass
class ApiRequest(BaseRequest):
    request_method: str = None
    method_slug: str = None
    cert: tuple[str, str] = None

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
        request_kwargs["cert"] = self.cert

        raw_response: requests.Response = requests.request(**request_kwargs)
        self.sent_requests.append(request_kwargs)
        return {"body": raw_response.text, "status_code": raw_response.status_code}


@dataclass
class LocalApiRequest(BaseRequest):
    handler: FunctionType = None
    s3_client: S3Client = None

    def _invoke(self, body: dict = None, **kwargs) -> dict:
        client_rp_details = ClientRpDetailsHeader.parse_raw(
            self.headers[CLIENT_RP_DETAILS]
        )
        connection_metadata = ConnectionMetadata.parse_raw(
            self.headers[CONNECTION_METADATA]
        )

        if connection_metadata.enable_permissions_lookup:
            ods_code = connection_metadata.ods_code
            app_id = client_rp_details.developer_app_id
            pointer_types = _parse_list_from_s3(
                s3_client=self.s3_client,
                bucket=AUTH_STORE,
                key=f"{app_id}/{ods_code}.json",
            )
        else:
            pointer_types = connection_metadata.pointer_types

        kwargs["authorizer"] = {"pointer-types": json.dumps(pointer_types)}
        event = make_aws_event(body=body, headers=self.headers, **kwargs)
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
    requestParams: dict[str] = None
    response: Response = None
    repositories: dict[BaseModel, FeatureTestRepository] = field(default_factory=dict)
    templates: dict[str, Template] = field(default_factory=dict)
    actor_context: ActorContext = None
    dynamodb_client: DynamoDbClient = None
    s3_client: S3Client = None
    auth_store: str = None
    environment_prefix: str = None
    rendered_templates: dict = field(default_factory=dict)


class Context(BehaveContext):
    test_config: TestConfig
