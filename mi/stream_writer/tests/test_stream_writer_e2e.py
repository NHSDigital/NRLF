import json
import string
from collections import ChainMap
from dataclasses import asdict, fields
from datetime import datetime as dt
from functools import partial

import pytest
from aws_lambda_powertools.utilities.data_classes.dynamo_db_stream_event import (
    DynamoDBRecordEventName,
)

from helpers.aws_session import new_aws_session
from helpers.terraform import get_terraform_json
from mi.reporting.actions import perform_query
from mi.reporting.resources import get_credentials, get_rds_endpoint
from mi.reporting.tests.test_data.generate_test_data import (
    FOREIGN_KEYS,
    Dimension,
    Measure,
)
from mi.sql_query.model import Sql, SqlQueryEvent
from mi.stream_writer.constants import DateTimeFormats
from mi.stream_writer.index import EVENT_CONFIG
from mi.stream_writer.model import Action, DynamoDBEventConfig, GoodResponse
from mi.stream_writer.tests.paths import PATH_TO_TEST_DATA
from mi.stream_writer.utils import hash_nhs_number

ASCII = list(string.ascii_lowercase + string.ascii_uppercase + string.digits)
RESOURCE_PREFIX = "nhsd-nrlf"
LAMBDA_NAME = RESOURCE_PREFIX + "--{workspace}--mi--stream_writer"
N_INITIAL_RECORDS = 1


def get_lambda_name(workspace: str) -> str:
    return LAMBDA_NAME.format(workspace=workspace)


def _create_report_query(credentials: dict, endpoint: str):
    with open(PATH_TO_TEST_DATA / "example_report.sql") as sql_file:
        statement = sql_file.read()

    return SqlQueryEvent(sql=Sql(statement=statement), endpoint=endpoint, **credentials)


def _create_dimensions_queries(credentials: dict, endpoint: str):
    queries = {}
    for dimension_type in FOREIGN_KEYS.values():
        _fields = ", ".join(field.name for field in fields(dimension_type))
        sql_statement = f"SELECT {_fields} FROM {dimension_type.name()}"
        query = SqlQueryEvent(
            sql=Sql(statement=sql_statement), endpoint=endpoint, **credentials
        )
        queries[dimension_type] = query
    return queries


def _create_fact_query(credentials: dict, endpoint: str):
    _fields = ", ".join(field.name for field in fields(Measure))
    return SqlQueryEvent(
        sql=Sql(statement=f"SELECT {_fields} FROM {Measure.name()}"),
        endpoint=endpoint,
        **credentials,
    )


def _dynamodb_stream_event(
    unique_id: str, created_on: str, image_type: str, event_name: str
) -> dict:
    event_path = PATH_TO_TEST_DATA / "dynamodb_stream_event.json"
    with open(event_path) as file:
        event_str = file.read()
    event_str = event_str.replace("<<UNIQUE_ID>>", unique_id)
    event_str = event_str.replace("<<CREATED_ON>>", created_on)
    event_str = event_str.replace("<<EVENT_NAME>>", event_name)
    event_str = event_str.replace("<<IMAGE_TYPE>>", image_type)
    return json.loads(event_str)  # noqa


def _invoke_stream_writer(session, workspace: str, event: dict) -> dict:
    client = session.client("lambda")
    function_name = get_lambda_name(workspace=workspace)
    result = client.invoke(FunctionName=function_name, Payload=json.dumps(event))
    response_payload = result["Payload"].read().decode("utf-8")
    if response_payload != json.dumps(asdict(GoodResponse())):
        pytest.fail(f"There was an error with the lambda:\n {response_payload}")


@pytest.fixture(scope="session")
def session():
    return new_aws_session()


@pytest.fixture(scope="session")
def env():
    tf_json = get_terraform_json()
    return tf_json["account_name"]["value"]


@pytest.fixture(scope="session")
def workspace():
    tf_json = get_terraform_json()
    return tf_json["workspace"]["value"]


@pytest.fixture(scope="session")
def report_query(credentials, endpoint):
    return _create_report_query(credentials=credentials, endpoint=endpoint)


@pytest.fixture(scope="session")
def dimension_queries(credentials, endpoint):
    return _create_dimensions_queries(credentials=credentials, endpoint=endpoint)


@pytest.fixture(scope="session")
def fact_query(credentials, endpoint):
    return _create_fact_query(credentials=credentials, endpoint=endpoint)


@pytest.fixture(scope="session")
def credentials(session, workspace):
    return get_credentials(session=session, workspace=workspace)


@pytest.fixture(scope="session")
def endpoint(session, env):
    return get_rds_endpoint(session=session, env=env)


def test_event_config_is_not_empty():
    """This test ensure that the e2e actually runs"""
    assert DynamoDBRecordEventName.INSERT in EVENT_CONFIG
    assert DynamoDBRecordEventName.REMOVE in EVENT_CONFIG
    assert DynamoDBRecordEventName.MODIFY not in EVENT_CONFIG


@pytest.mark.parametrize("event_config", EVENT_CONFIG.items())
@pytest.mark.integration
def test_e2e_with_report(
    session,
    workspace,
    report_query: SqlQueryEvent,
    dimension_queries: dict[type[Dimension], SqlQueryEvent],
    fact_query: SqlQueryEvent,
    event_config: tuple[DynamoDBRecordEventName, DynamoDBEventConfig],
):
    # This function will get the report for
    # "mi/stream_writer/tests/queries/test_report.sql"
    execute_report_query = partial(
        perform_query,
        session=session,
        workspace=workspace,
        event=report_query,
    )
    execute_fact_query = partial(
        perform_query,
        session=session,
        workspace=workspace,
        event=fact_query,
    )
    execute_dimensions_query = {
        dimension_type: partial(
            perform_query, session=session, workspace=workspace, event=query
        )
        for dimension_type, query in dimension_queries.items()
    }
    # Create the test event (use timestamp as unique id to force create new dimensions)
    event_name, config = event_config
    timestamp = dt.now()
    unique_id = timestamp.strftime(DateTimeFormats.DOCUMENT_POINTER_FORMAT)
    event = _dynamodb_stream_event(
        unique_id=unique_id,
        created_on=unique_id,
        event_name=event_name.name,
        image_type=config.image_type,
    )

    # Invoke the lambda with a large initial event
    # to ensure that there is some initial state in the db
    records = []
    for i in range(N_INITIAL_RECORDS):
        _event = _dynamodb_stream_event(
            unique_id=unique_id + str(i),
            created_on=unique_id,
            event_name=event_name.name,
            image_type=config.image_type,
        )
        records += _event["Records"]
    _invoke_stream_writer(
        session=session, workspace=workspace, event={"Records": records}
    )

    # Get the initial state of the report to use later to perform a diff
    initial_report = execute_report_query()
    initial_facts = execute_fact_query()
    initial_dimensions = []
    for dimension_type, _execute_dimensions_query in execute_dimensions_query.items():
        initial_dimensions += [
            dimension_type(**item) for item in _execute_dimensions_query()
        ]
    assert len(initial_report) >= N_INITIAL_RECORDS
    assert len(initial_facts) >= N_INITIAL_RECORDS

    # Create the test event (use timestamp as unique id to force create new dimensions)
    event_name, config = event_config
    timestamp = dt.now()
    unique_id = timestamp.strftime(DateTimeFormats.DOCUMENT_POINTER_FORMAT)
    event = _dynamodb_stream_event(
        unique_id=unique_id,
        event_name=event_name.name,
        image_type=config.image_type,
        created_on=unique_id,
    )

    # Invoke the lambda to fake a dynamodb stream event
    _invoke_stream_writer(session=session, workspace=workspace, event=event)

    # Get the final state of the report
    # "mi/stream_writer/tests/queries/test_report.sql"
    # plus queries for the core dimensions and fact items
    final_report = execute_report_query()
    final_facts = execute_fact_query()
    final_dimensions = []
    for dimension_type, _execute_dimensions_query in execute_dimensions_query.items():
        final_dimensions += [
            dimension_type(**item) for item in _execute_dimensions_query()
        ]

    # Check 1: Initial state is a subset of the final state
    assert all(item in final_report for item in initial_report)
    assert all(item in final_facts for item in initial_facts)
    assert all(item in final_dimensions for item in initial_dimensions)

    # Check 2: There is one new row in the final state, corresponding to our report
    (new_report_item,) = filter(lambda item: item not in initial_report, final_report)

    # Check 3: The report is as expected
    assert (
        new_report_item
        == {  # Fields here map on to mi/stream_writer/tests/queries/test_report.sql
            "provider_name": f"provider-{unique_id}",
            "patient": hash_nhs_number(f"patient-{unique_id}"),
            "document_type_code": f"document-{unique_id}",
            "document_type_system": "http://snomed.info/sct",
            "day": timestamp.day,
            "month": timestamp.strftime("%b"),
            "year": timestamp.year,
            "count_created": 1 if config.action is Action.CREATED else 0,
            "count_deleted": 1 if config.action is Action.DELETED else 0,
        }
    )

    # Check 4: Expect one new dimension item per type
    new_dimensions = list(
        filter(lambda item: item not in initial_dimensions, final_dimensions)
    )
    assert sorted(
        (type(item) for item in new_dimensions), key=lambda cls: cls.__name__
    ) == sorted(FOREIGN_KEYS.values(), key=lambda cls: cls.__name__)

    # Check 5: Expect the dimensions are consistent with the input data
    combined_dimensions = ChainMap(*map(asdict, new_dimensions))
    assert combined_dimensions["provider_name"] == f"provider-{unique_id}"
    assert combined_dimensions["patient_hash"] == hash_nhs_number(
        f"patient-{unique_id}"
    )
    assert combined_dimensions["document_type_code"] == f"document-{unique_id}"

    # Check 6: Expect one new fact, consistent with the input data
    # and the new dimensions
    (new_fact,) = filter(lambda fact: fact not in initial_facts, final_facts)
    assert Measure(**new_fact) == Measure(
        provider_id=combined_dimensions["provider_id"],
        patient_id=combined_dimensions["patient_id"],
        document_type_id=combined_dimensions["document_type_id"],
        day=timestamp.day,
        month=timestamp.month,
        year=timestamp.year,
        day_of_week=timestamp.weekday(),
        count_created=1 if config.action is Action.CREATED else 0,
        count_deleted=1 if config.action is Action.DELETED else 0,
    )


@pytest.mark.integration
def test_e2e_modify_events_do_nothing(
    session,
    workspace,
    report_query: SqlQueryEvent,
    dimension_queries: dict[type[Dimension], SqlQueryEvent],
    fact_query: SqlQueryEvent,
):
    # This function will get the report for
    # "mi/stream_writer/tests/queries/test_report.sql"
    execute_report_query = partial(
        perform_query,
        session=session,
        workspace=workspace,
        event=report_query,
    )
    execute_fact_query = partial(
        perform_query,
        session=session,
        workspace=workspace,
        event=fact_query,
    )
    execute_dimensions_query = {
        dimension_type: partial(
            perform_query, session=session, workspace=workspace, event=query
        )
        for dimension_type, query in dimension_queries.items()
    }

    # Get the initial state of the report to use later to perform a diff
    initial_report = execute_report_query()
    initial_facts = execute_fact_query()
    initial_dimensions = []
    for dimension_type, _execute_dimensions_query in execute_dimensions_query.items():
        initial_dimensions += [
            dimension_type(**item) for item in _execute_dimensions_query()
        ]

    # Create the test event (use timestamp as unique id to force create new dimensions)
    timestamp = dt.now()
    unique_id = timestamp.strftime(DateTimeFormats.DOCUMENT_POINTER_FORMAT)
    event = _dynamodb_stream_event(
        unique_id=unique_id, event_name="MODIFY", image_type="", created_on=unique_id
    )

    # Invoke the lambda to fake a dynamodb stream event
    _invoke_stream_writer(session=session, workspace=workspace, event=event)

    # Get the final state of the report
    # "mi/stream_writer/tests/queries/test_report.sql"
    # plus queries for the core dimensions and fact items
    final_report = execute_report_query()
    final_facts = execute_fact_query()
    final_dimensions = []
    for dimension_type, _execute_dimensions_query in execute_dimensions_query.items():
        final_dimensions += [
            dimension_type(**item) for item in _execute_dimensions_query()
        ]

    # Check 1: Initial state is a subset of the final state
    assert final_report == initial_report
    assert final_facts == initial_facts
    assert final_dimensions == initial_dimensions
