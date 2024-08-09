import os
import uuid
from enum import Enum

from scripts.aws_session_assume import get_account_name
from tests.utilities.api_clients import ClientConfig, ConnectionMetadata
from tests.utilities.get_access_token import get_bearer_token


class SmokeTestParameters:
    def __init__(self, parameters: dict[str, str]):
        self.public_base_url = parameters.get("public_base_url")
        self.apigee_app_id = parameters.get("apigee_app_id")
        self.apigee_app_name = parameters.get("apigee_app_name")
        self.nrlf_app_id = parameters.get("nrlf_app_id")
        self.ods_code = parameters.get("ods_code")
        self.test_nhs_numbers = parameters.get("test_nhs_numbers").split(",")


class ConnectMode(Enum):
    # INTERNAL connect mode is for connecting to the NRLF via internal access methods
    INTERNAL = "internal"
    # Public connect mode is for connecting to the NRLF via public access methods
    PUBLIC = "public"


class EnvironmentConfig:

    def __init__(self):
        self.env_name = os.getenv("TEST_ENVIRONMENT_NAME")
        self.stack_name = os.getenv("TEST_STACK_NAME", None)
        self.connect_mode = os.getenv("TEST_CONNECT_MODE")

        domain_name = os.getenv("TEST_STACK_DOMAIN")
        self.internal_base_url = f"https://{domain_name}/"

    def get_parameters_name(self):
        return f"nhsd-nrlf--{self.env_name}--smoke-test-parameters"

    def to_client_config(self, parameters: SmokeTestParameters):
        connection_metadata = ConnectionMetadata.parse_obj(
            {
                "nrl.ods-code": parameters.ods_code,
                "nrl.permissions": [],
                "nrl.app-id": parameters.nrlf_app_id,
                "client_rp_details": {
                    "developer.app.name": parameters.apigee_app_name,
                    "developer.app.id": parameters.apigee_app_id,
                },
            }
        )

        smoketest_id = str(uuid.uuid4())

        if self.connect_mode == ConnectMode.INTERNAL.value:
            return ClientConfig(
                base_url=self.internal_base_url,
                custom_headers={
                    "X-Request-Id": smoketest_id,
                    "NHSD-Correlation-Id": f"{smoketest_id}.smoketest.{self.stack_name}.{self.env_name}",
                },
                connection_metadata=connection_metadata,
                client_cert=(
                    f"./truststore/client/{self.env_name}.crt",
                    f"./truststore/client/{self.env_name}.key",
                ),
            )
        elif self.connect_mode == ConnectMode.PUBLIC.value:
            account_name = get_account_name(self.env_name)
            auth_token = get_bearer_token(
                account_name, parameters.apigee_app_id, self.env_name
            )
            return ClientConfig(
                base_url=parameters.public_base_url,
                custom_headers={
                    "X-Request-Id": smoketest_id,
                    "NHSD-End-User-Organisation-ODS": parameters.ods_code,
                },
                auth_token=auth_token,
                api_path="/FHIR/R4",
            )

        raise ValueError(f"Invalid connect mode: {self.connect_mode}")
