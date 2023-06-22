import json
from dataclasses import asdict
from typing import Union

from behave import use_fixture
from lambda_utils.header_config import ClientRpDetailsHeader, ConnectionMetadata

from feature_tests.common.constants import (
    ALLOWED_APP_IDS,
    ALLOWED_APPS,
    DEFAULT_VERSION,
    TABLE_CONFIG,
    Action,
    TestMode,
)
from feature_tests.common.fixtures import (
    mock_dynamodb,
    mock_environmental_variables,
    mock_s3,
    setup_buckets,
    setup_tables,
)
from feature_tests.common.models import (
    ActorContext,
    ApiRequest,
    AuthLambdaRequest,
    Context,
    LocalApiRequest,
    LocalAuthLambdaRequest,
    TestConfig,
)
from feature_tests.common.repository import FeatureTestRepository
from feature_tests.common.utils import (
    get_api_definitions_from_swagger,
    get_dynamodb_client,
    get_endpoint,
    get_environment_prefix,
    get_lambda_arn,
    get_lambda_client,
    get_lambda_handler,
    get_permissions_bucket,
    get_s3_client,
    get_test_mode,
    get_tls_ma_files,
)
from nrlf.core.constants import (
    CLIENT_RP_DETAILS,
    CONNECTION_METADATA,
    PERMISSION_AUDIT_DATES_FROM_PAYLOAD,
)
from nrlf.core.types import S3Client
from nrlf.core.validators import json_loads


def _local_mock(context: Context):
    use_fixture(mock_environmental_variables, context)
    use_fixture(mock_dynamodb, context)
    use_fixture(mock_s3, context)
    setup_tables()
    setup_buckets()


def request_setup(
    context: Context, actor: str, org_id: str, actor_type: str, action: str
) -> Union[ApiRequest, LocalApiRequest, AuthLambdaRequest, LocalAuthLambdaRequest]:
    test_config: TestConfig = context.test_config

    actor_context = ActorContext(
        actor=actor, org_id=org_id, actor_type=actor_type, action=action
    )
    test_config.actor_context = actor_context

    base_request_config = asdict(test_config.request)
    del base_request_config["endpoint"]

    request = None
    if actor_context.action is Action.authoriser:
        if test_config.mode is TestMode.LOCAL_TEST:
            handler = get_lambda_handler(
                actor_type=actor_context.actor_type, action=actor_context.action
            )
            request = LocalAuthLambdaRequest(**base_request_config, handler=handler)
        else:
            arn = get_lambda_arn(
                test_mode=test_config.mode, actor_type=actor_context.actor_type
            )
            lambda_client = get_lambda_client(test_mode=test_config.mode)
            request = AuthLambdaRequest(
                **base_request_config, endpoint=arn, lambda_client=lambda_client
            )
    else:
        if test_config.mode is TestMode.LOCAL_TEST:
            handler = get_lambda_handler(
                actor_type=actor_context.actor_type,
                action=actor_context.action,
                suffix="DocumentReference",
            )
            request = LocalApiRequest(
                **base_request_config, handler=handler, s3_client=test_config.s3_client
            )
        else:
            api_definitions = get_api_definitions_from_swagger(
                actor_type=actor_context.actor_type
            )
            api_definition = api_definitions[actor_context.action.name]
            endpoint = get_endpoint(
                test_mode=test_config.mode, actor_type=actor_context.actor_type
            )
            cert = get_tls_ma_files(test_mode=test_config.mode)
            request = ApiRequest(
                **base_request_config, endpoint=endpoint, cert=cert, **api_definition
            )
    request.version = DEFAULT_VERSION
    return request


def config_setup(context: Context, scenario_name: str) -> TestConfig:
    test_mode = get_test_mode(context=context)
    if test_mode is TestMode.LOCAL_TEST:
        _local_mock(context=context)
    environment_prefix = get_environment_prefix(test_mode=test_mode)
    permissions_bucket = get_permissions_bucket(test_mode=test_mode)
    dynamodb_client = get_dynamodb_client(test_mode=test_mode)
    s3_client = get_s3_client(test_mode=test_mode)
    repositories = {
        table: FeatureTestRepository(
            item_type=table,
            client=dynamodb_client,
            environment_prefix=environment_prefix,
        )
        for table in TABLE_CONFIG.keys()
    }
    test_config = TestConfig(mode=test_mode, repositories=repositories)
    test_config.request.scenario_name = scenario_name
    test_config.dynamodb_client = dynamodb_client
    test_config.s3_client = s3_client
    test_config.environment_prefix = environment_prefix
    test_config.permissions_bucket = permissions_bucket
    return test_config


def register_application(
    context: Context,
    org_id: str,
    org_id_extension: str,
    app_name: str,
    app_id: str,
    pointer_types: list[str],
    enable_s3_for_permissions: bool,
):
    test_config: TestConfig = context.test_config
    if app_name not in ALLOWED_APPS:
        raise ValueError(f"App name {app_name} must be one of {ALLOWED_APPS}")

    if app_id not in ALLOWED_APP_IDS:
        raise ValueError(f"App ID {app_id} must be one of {ALLOWED_APP_IDS}")

    connection_metadata = {
        "nrl.ods-code": org_id,
        "nrl.ods-code-extension": org_id_extension,
        "nrl.enable-permissions-lookup": enable_s3_for_permissions,
    }
    if enable_s3_for_permissions:
        register_pointer_types_in_s3(
            app_id=app_id,
            org_id=org_id,
            pointer_types=pointer_types,
            s3_client=context.test_config.s3_client,
            permissions_bucket=test_config.permissions_bucket,
        )
    if not enable_s3_for_permissions:
        connection_metadata["nrl.pointer-types"] = pointer_types

    test_config.request.headers[CONNECTION_METADATA] = ConnectionMetadata(
        **connection_metadata
    ).json(by_alias=True)

    test_config.request.headers[CLIENT_RP_DETAILS] = ClientRpDetailsHeader(
        **{"developer.app.name": app_name, "developer.app.id": app_id}
    ).json(by_alias=True)


def set_audit_date_permission(context: Context):
    test_config = context.test_config
    existing_headers = json_loads(test_config.request.headers[CONNECTION_METADATA])
    existing_headers["nrl.permissions"].append(PERMISSION_AUDIT_DATES_FROM_PAYLOAD)
    test_config.request.headers[CONNECTION_METADATA] = json.dumps(existing_headers)


def register_pointer_types_in_s3(
    app_id: str,
    org_id: str,
    pointer_types: list[str],
    s3_client: S3Client,
    permissions_bucket: str,
):
    s3_client.put_object(
        Bucket=permissions_bucket,
        Key=f"{app_id}/{org_id}.json",
        Body=json.dumps(pointer_types).encode(),
    )
