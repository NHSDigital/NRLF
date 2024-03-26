import os

import boto3
from behave.runner import Context

from tests.features.utils.certificates import get_cert_path_for_environment

os.environ.setdefault("SPLUNK_INDEX", "logs")
os.environ.setdefault("POWERTOOLS_LOG_LEVEL", "ERROR")


from nrlf.core.dynamodb.repository import DocumentPointerRepository


def before_all(context: Context):
    """
    This function is called before all the tests are executed
    """
    context.env = context.config.userdata.get("env")
    context.base_url = f"https://{context.env}.api.record-locator.dev.national.nhs.uk/"

    context.client_cert = get_cert_path_for_environment(context.env)
    context.repository = DocumentPointerRepository(
        dynamodb=boto3.resource("dynamodb", region_name="eu-west-2"),
        environment_prefix=f"nhsd-nrlf--{context.env}--",
    )

    # context.client = ConsumerClient(
    #     config=ClientConfig(
    #         base_url=context.base_url,
    #         client_cert=context.client_cert,
    #         connection_metadata=ConnectionMetadata.parse_obj({
    #             "nrl.pointer-types": [],
    #             "nrl.ods-code": "X26",
    #             "nrl.ods-code-extension": False,
    #             "nrl.permissions": [],
    #             "client_rp_details": {
    #                 "developer.app.name": "NRLF Test Harness",
    #                 "developer.app.id": "NRLF-TEST-HARNESS"
    #             }
    #         })
    #     )
    # )
