from behave.runner import Context

from nrlf.core.model import ConnectionMetadata
from tests.utilities.api_clients import (
    ClientConfig,
    ConsumerTestClient,
    ProducerTestClient,
)


def _config_from_context(context: Context, ods_code: str):
    ods_code_parts = ods_code.split(".", 1)
    ods_code_extension = None
    if len(ods_code_parts) == 2:
        ods_code_extension = ods_code_parts[1]

    feature_test_headers = {
        "X-Request-Id": context.request_id,
        "NHSD-Correlation-Id": context.correlation_id,
    }

    return ClientConfig(
        base_url=context.base_url,
        custom_headers=feature_test_headers,
        client_cert=context.client_cert,
        connection_metadata=ConnectionMetadata.model_validate(
            {
                "nrl.ods-code": ods_code_parts[0],
                "nrl.ods-code-extension": ods_code_extension,
                "nrl.permissions": [],
                "nrl.app-id": context.application.app_id,
                "client_rp_details": {
                    "developer.app.name": context.application.app_name,
                    "developer.app.id": context.application.app_id,
                },
            }
        ),
    )


def consumer_client_from_context(context: Context, ods_code: str):
    client_config = _config_from_context(context, ods_code)
    return ConsumerTestClient(config=client_config)


def producer_client_from_context(context: Context, ods_code: str):
    client_config = _config_from_context(context, ods_code)
    return ProducerTestClient(config=client_config)
