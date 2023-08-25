import os
from datetime import datetime as dt
from unittest import mock

from mi.stream_writer.constants import DateTimeFormats
from mi.stream_writer.event_handling import catch_error
from mi.stream_writer.index import _handler, handler
from mi.stream_writer.model import (
    Environment,
    ErrorResponse,
    GoodResponse,
    MiResponses,
    Status,
)
from mi.stream_writer.tests.stream_writer_helpers import dynamodb_stream_event

IMPORT_PREFIX = "mi.stream_writer.index"


@mock.patch(f"{IMPORT_PREFIX}.insert_mi_record")
@mock.patch(f"{IMPORT_PREFIX}.boto3")
@mock.patch(f"{IMPORT_PREFIX}.psycopg2")
def test__handler_populates_success_responses(
    mock_psycopg2, boto3, mock_insert_mi_record
):
    environment = mock.Mock()
    secrets_manager = mock.Mock()

    mock_insert_mi_record.side_effect = catch_error()(
        lambda *args, **kwargs: GoodResponse()
    )

    timestamp = dt.now()
    unique_id = timestamp.strftime(DateTimeFormats.DOCUMENT_POINTER_FORMAT)

    event = dynamodb_stream_event(
        unique_id=unique_id,
        created_on=unique_id,
        event_name="INSERT",
        image_type="NewImage",
    )

    responses = MiResponses()

    _handler(
        event=event,
        responses=responses,
        environment=environment,
        secrets_manager=secrets_manager,
    )

    assert len(responses.successful_responses) == 1


@mock.patch.dict(
    os.environ,
    {
        "POSTGRES_DATABASE_NAME": "thing",
        "RDS_CLUSTER_HOST": "thing",
        "RDS_CLUSTER_PORT": "11",
        "POSTGRES_USERNAME": "thing",
        "POSTGRES_PASSWORD": "thing",  # pragma: allowlist secret
        "MI_S3_ERROR_BUCKET": "thing",
    },
)
@mock.patch(f"{IMPORT_PREFIX}.insert_mi_record")
@mock.patch(f"{IMPORT_PREFIX}.boto3")
@mock.patch(f"{IMPORT_PREFIX}.psycopg2")
def test_handler_populates_responses(mock_psycopg2, boto3, mock_insert_mi_record):
    timestamp = dt.now()
    unique_id = timestamp.strftime(DateTimeFormats.DOCUMENT_POINTER_FORMAT)

    event = dynamodb_stream_event(
        unique_id=unique_id,
        created_on=unique_id,
        event_name="INSERT",
        image_type="NewImage",
    )
    secrets_manager = mock.Mock()

    mock_insert_mi_record.side_effect = catch_error()(
        lambda *args, **kwargs: GoodResponse()
    )

    responses = handler(event=event, secrets_manager=secrets_manager)
    responses = MiResponses(**responses)

    assert len(responses.successful_responses) == 1


@mock.patch.dict(
    os.environ,
    {
        "POSTGRES_DATABASE_NAME": "thing",
        "RDS_CLUSTER_HOST": "thing",
        "RDS_CLUSTER_PORT": "11",
        "POSTGRES_USERNAME": "thing",
        "POSTGRES_PASSWORD": "thing",  # pragma: allowlist secret
        "MI_S3_ERROR_BUCKET": "thing",
    },
)
@mock.patch(f"{IMPORT_PREFIX}.insert_mi_record")
@mock.patch(f"{IMPORT_PREFIX}.boto3")
@mock.patch(f"{IMPORT_PREFIX}.psycopg2")
@mock.patch(f"{IMPORT_PREFIX}.send_errors_to_s3")
def test_handler(mock_send_errors_s3, mock_psycopg2, boto3, mock_insert_mi_record):
    timestamp = dt.now()
    unique_id = timestamp.strftime(DateTimeFormats.DOCUMENT_POINTER_FORMAT)

    event = dynamodb_stream_event(
        unique_id=unique_id,
        created_on=unique_id,
        event_name="INSERT",
        image_type="NewImage",
    )
    secrets_manager = mock.Mock()
    s3_client = mock.Mock()

    class BadError(Exception):
        pass

    expected_error = ErrorResponse(
        error="The record is bad",
        error_type="BadError",
        function="mi.stream_writer.index._handler",
        trace="no",
        status=Status.ERROR,
        metadata={"event": event},
    )

    mock_insert_mi_record.side_effect = BadError("The record is bad")

    responses = handler(
        event=event, secrets_manager=secrets_manager, s3_client=s3_client
    )

    # This happens because we turn responses into a string
    responses = MiResponses(**responses)

    responses.error_responses = [ErrorResponse(**responses.error_responses[0])]
    error_response = responses.error_responses[0]

    mock_send_errors_s3.assert_called_once_with(
        responses=responses, environment=Environment.construct(), s3_client=s3_client
    )

    assert error_response.error == expected_error.error
    assert error_response.error_type == expected_error.error_type
    assert error_response.function == expected_error.function
    assert error_response.status == expected_error.status
