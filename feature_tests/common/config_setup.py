import json
from dataclasses import asdict
from typing import Union

from behave import use_fixture
from behave.runner import Context
from nrlf.core.errors import ItemNotFound
from nrlf.core.model import AuthBase, AuthConsumer, AuthProducer
from nrlf.core.query import create_read_and_filter_query

from feature_tests.common.constants import (
    ALLOWED_APP_IDS,
    ALLOWED_APPS,
    DEFAULT_VERSION,
    TABLE_CONFIG,
    Action,
    ActorType,
    TestMode,
)
from feature_tests.common.fixtures import (
    mock_dynamodb,
    mock_environmental_variables,
    setup_tables,
)
from feature_tests.common.models import (
    ActorContext,
    ApiRequest,
    AuthLambdaRequest,
    LocalApiRequest,
    LocalAuthLambdaRequest,
    TestConfig,
)
from feature_tests.common.utils import (
    get_api_definitions_from_swagger,
    get_dynamodb_client,
    get_endpoint,
    get_environment_prefix,
    get_lambda_arn,
    get_lambda_client,
    get_lambda_handler,
    get_test_mode,
)
from helpers.seed_data_repository import SeedDataRepository


def _local_mock(context: Context):
    use_fixture(mock_environmental_variables, context)
    use_fixture(mock_dynamodb, context)
    setup_tables()


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
            request = LocalApiRequest(**base_request_config, handler=handler)
        else:
            api_definitions = get_api_definitions_from_swagger(
                actor_type=actor_context.actor_type
            )
            api_definition = api_definitions[actor_context.action.name]
            endpoint = get_endpoint(
                test_mode=test_config.mode, actor_type=actor_context.actor_type
            )
            request = ApiRequest(
                **base_request_config, endpoint=endpoint, **api_definition
            )
    request.version = DEFAULT_VERSION
    return request


def config_setup(context: Context, scenario_name: str) -> TestConfig:
    test_mode = get_test_mode(context=context)
    if test_mode is TestMode.LOCAL_TEST:
        _local_mock(context=context)
    environment_prefix = get_environment_prefix(test_mode=test_mode)
    dynamodb_client = get_dynamodb_client(test_mode=test_mode)
    repositories = {
        table: SeedDataRepository(
            item_type=table,
            client=dynamodb_client,
            environment_prefix=environment_prefix,
        )
        for table in TABLE_CONFIG.keys()
    }
    test_config = TestConfig(
        mode=test_mode,
        repositories=repositories,
    )
    test_config.request.scenario_name = scenario_name
    return test_config


def register_application(context: Context, org_id: str, app_name: str, app_id: str):
    test_config: TestConfig = context.test_config
    if app_name not in ALLOWED_APPS:
        raise ValueError(f"App name {app_name} must be one of {ALLOWED_APPS}")

    if app_id not in ALLOWED_APP_IDS:
        raise ValueError(f"App ID {app_id} must be one of {ALLOWED_APP_IDS}")

    auth_model = (
        AuthProducer
        if test_config.actor_context.actor_type is ActorType.Producer
        else AuthConsumer
    )
    auth_repository = test_config.repositories[auth_model]
    auth: Union[AuthProducer, AuthConsumer] = auth_model(
        id=org_id,
        application_id=app_id,
        pointer_types=[f'{row["system"]}|{row["value"]}' for row in context.table],
    )
    auth_repository.create(auth)


def mock_local_auth(test_config: TestConfig, org_id: str):
    auth_model = (
        AuthProducer
        if test_config.actor_context.actor_type is ActorType.Producer
        else AuthConsumer
    )
    authentication_query = create_read_and_filter_query(id=org_id)
    try:
        auth: AuthBase = test_config.repositories[auth_model].read(
            **authentication_query
        )
    except ItemNotFound:
        pass
    else:
        pointer_types = auth.pointer_types.__root__
        test_config.request.headers["pointer-types"] = (
            json.dumps(pointer_types)
            if test_config.actor_context.action is Action.authoriser
            else pointer_types
        )
