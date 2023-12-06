import json
import string
import time
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
from mi.stream_writer.index import EVENT_CONFIG
from mi.stream_writer.model import Action, DynamoDBEventConfig, MiResponses
from mi.stream_writer.tests.paths import PATH_TO_TEST_DATA
from mi.stream_writer.tests.stream_writer_helpers import dynamodb_stream_event
from mi.stream_writer.utils import hash_nhs_number
from nrlf.core.types import DynamoDbClient
from nrlf.core.validators import json_loads

ASCII = list(string.ascii_lowercase + string.ascii_uppercase + string.digits)
RESOURCE_PREFIX = "nhsd-nrlf"
LAMBDA_NAME = RESOURCE_PREFIX + "--{workspace}--mi--stream_writer"
N_INITIAL_RECORDS = 20


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


def _invoke_stream_writer(session, workspace: str, event: dict) -> MiResponses:
    client = session.client("lambda")
    function_name = get_lambda_name(workspace=workspace)
    result = client.invoke(FunctionName=function_name, Payload=json.dumps(event))
    response_payload = result["Payload"].read().decode("utf-8")
    response: dict = json_loads(response_payload)
    return MiResponses(**response)


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
def table_name():
    tf_json = get_terraform_json()
    return tf_json["dynamodb"]["value"]["document_pointer"]["name"]


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
    table_name: str,
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

    # Unique identifiers for this test
    event_name, config = event_config
    timestamp = dt.now()
    unique_id = timestamp.isoformat()
    event = dynamodb_stream_event(
        unique_id=unique_id,
        created_on=unique_id,
        event_name=event_name.name,
        image_type=config.image_type,
    )

    # Invoke the lambda with a large initial event
    # to ensure that there is some initial state in the db
    records = []
    for i in range(N_INITIAL_RECORDS):
        _event = dynamodb_stream_event(
            unique_id=unique_id + str(i),
            created_on=unique_id,
            event_name=event_name.name,
            image_type=config.image_type,
        )
        records += _event["Records"]
    assert len(records) == N_INITIAL_RECORDS
    response = _invoke_stream_writer(
        session=session, workspace=workspace, event={"Records": records}
    )
    assert (
        len(response.error_responses) + len(response.successful_responses)
        == N_INITIAL_RECORDS
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

    # # Invoke the lambda to fake a dynamodb stream event
    # _invoke_stream_writer(session=session, workspace=workspace, event=event)
    (record,) = event["Records"]
    _document_pointer: dict = record["dynamodb"][config.image_type]
    dynamodb_client: DynamoDbClient = session.client("dynamodb")
    dynamodb_client.put_item(Item=_document_pointer, TableName=table_name)
    if event_name == DynamoDBRecordEventName.REMOVE:
        dynamodb_client.delete_item(
            Key={"pk": _document_pointer["pk"], "sk": _document_pointer["sk"]},
            TableName=table_name,
        )
    time.sleep(5)

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
            "count_created": 1,
            "count_deleted": int(config.action is Action.DELETED),
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
        count_created=1,
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
    unique_id = timestamp.isoformat()
    event = dynamodb_stream_event(
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


@pytest.mark.integration
def test_e2e_s3_bucket_is_populated(
    session,
    workspace,
    report_query: SqlQueryEvent,
    dimension_queries: dict[type[Dimension], SqlQueryEvent],
    fact_query: SqlQueryEvent,
):
    # Create the test event (use timestamp as unique id to force create new dimensions)
    timestamp = dt.now()
    unique_id = timestamp.isoformat()
    event = dynamodb_stream_event(
        unique_id=unique_id,
        event_name="INSERT",
        image_type="NewImage",
        created_on=unique_id,
    )
    event_id = "test_event_id"
    event["Records"][0]["eventID"] = event_id

    record: dict = event["Records"][0]["dynamodb"]["NewImage"]
    record.pop("custodian")

    responses = _invoke_stream_writer(session=session, workspace=workspace, event=event)

    unique_id = responses.unique_id
    bucket_key = f"{unique_id}/{event_id}.json"
    s3_client = session.client("s3")

    tf_json = get_terraform_json()
    bucket_name = tf_json["mi"]["value"]["s3_mi_errors_bucket"]

    error_object = s3_client.get_object(
        Bucket=bucket_name,
        Key=bucket_key,
    )
    response_payload = error_object["Body"].read().decode("utf-8")
    response: dict = json_loads(response_payload)

    assert (
        response["error"]
        == "from_document_pointer() missing 1 required positional argument: 'custodian'"
    )
    assert response["error_type"] == "TypeError"
    assert response["function"] == "mi.stream_writer.index._handler"
    assert response["status"] == "ERROR"
    assert response["metadata"] == {"event": event}
