import os

from behave.runner import Context

from tests.features.utils.certificates import get_cert_path_for_environment

os.environ.setdefault("POWERTOOLS_LOG_LEVEL", "ERROR")
os.environ.setdefault("AWS_DEFAULT_REGION", "eu-west-2")

from nrlf.core.dynamodb.repository import DocumentPointerRepository


def before_all(context: Context):
    """
    This function is called before all the tests are executed
    """

    context.env = context.config.userdata.get("env")
    context.base_url = f"https://{context.env}.api.record-locator.dev.national.nhs.uk/"

    default_table_name = f"nhsd-nrlf--{context.env}-pointers-table"
    os.environ.setdefault("TABLE_NAME", default_table_name)

    context.client_cert = get_cert_path_for_environment(context.env)
    context.repository = DocumentPointerRepository(
        table_name=default_table_name
    )
