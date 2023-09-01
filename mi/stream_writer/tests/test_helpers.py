import string
from unittest import mock

import pytest
from aws_lambda_powertools.utilities.data_classes.dynamo_db_stream_event import (
    StreamRecord,
)
from hypothesis import given
from hypothesis.strategies import (
    booleans,
    builds,
    dictionaries,
    from_regex,
    lists,
    sampled_from,
    text,
)

from mi.stream_writer.event_handling import _execute_sql, catch_error, insert_mi_record
from mi.stream_writer.model import (
    DIMENSION_TYPES,
    Dimension,
    ErrorResponse,
    GoodResponse,
    MiResponses,
    RecordParams,
)
from mi.stream_writer.psycopg2 import connection as Connection
from mi.stream_writer.psycopg2 import cursor as Cursor
from mi.stream_writer.utils import hash_nhs_number, is_document_pointer, to_snake_case

ASCII = list(string.ascii_lowercase + string.ascii_uppercase + string.digits)


@pytest.mark.parametrize(
    "camel_case, expected_snake_case",
    [
        ("UpperCamelCase", "upper_camel_case"),
        ("AnotherExampleCase", "another_example_case"),
        ("SomeVariableName", "some_variable_name"),
        ("HTTPRequestHandler", "http_request_handler"),
        ("HTMLParser", "html_parser"),
    ],
)
def test_to_snake_case(camel_case, expected_snake_case):
    assert to_snake_case(camel_case=camel_case) == expected_snake_case


@pytest.mark.parametrize(
    "nhs_number, expected_hash",
    [
        (
            "1234567890",
            "c775e7b757ede630cd0aa1113bd102661ab38829ca52a6422ab782862f268646",  # pragma: allowlist secret
        ),
        (
            "9876543210",
            "7619ee8cea49187f309616e30ecf54be072259b43760f1f550a644945d5572f2",  # pragma: allowlist secret
        ),
        (
            "5555555555",
            "a5ad7e6d5225ad00c5f05ddb6bb3b1597a843cc92f6cf188490ffcb88a1ef4ef",  # pragma: allowlist secret
        ),
        (
            "1111111111",
            "d2d02ea74de2c9fab1d802db969c18d409a8663a9697977bb1c98ccdd9de4372",  # pragma: allowlist secret
        ),
        (
            "9999999999",
            "ce3a598687c8d2e5aa6bedad20e059b4a78cca0adad7e563b07998d5cd226b8c",  # pragma: allowlist secret
        ),
    ],
)
def test_hash_nhs_number(nhs_number, expected_hash):
    assert hash_nhs_number(nhs_number=nhs_number) == expected_hash


@given(
    is_error=booleans(),
    kwargs=dictionaries(
        keys=text(alphabet=ASCII, min_size=1), values=text(alphabet=ASCII)
    ),
)
def test_catch_error(is_error, kwargs: dict):
    class MyException(Exception):
        pass

    ERROR_MSG = "oh, no!"

    responses = MiResponses()

    @catch_error(log_fields=kwargs.keys())
    def wrapped_function(is_error, responses, **kwargs):
        if is_error:
            raise MyException(ERROR_MSG)
        return GoodResponse()

    response = wrapped_function(is_error=is_error, responses=responses, **kwargs)
    expected_response = (
        ErrorResponse(
            error=ERROR_MSG,
            error_type="MyException",
            function="test_helpers.wrapped_function",
            trace="trace",
            metadata=kwargs,
        )
        if is_error
        else GoodResponse()
    )
    if type(response) is ErrorResponse:
        response.trace = "trace"

    assert response == expected_response


@mock.patch("mi.stream_writer.event_handling.psycopg2_sql")
def test__execute_sql_rollback(mocked_sql):
    class MyException(Exception):
        pass

    def _raise(err: Exception):
        raise err

    mocked_cursor = mock.Mock(spec=Cursor)
    mocked_cursor.connection = mock.Mock(spec=Connection)
    mocked_cursor.execute.side_effect = lambda *args, **kwargs: _raise(MyException())

    with pytest.raises(MyException):
        _execute_sql(
            cursor=mocked_cursor, statement=None, params=None, identifiers=None
        )
    mocked_cursor.connection.rollback.assert_called()


@mock.patch("mi.stream_writer.event_handling.psycopg2_sql")
def test_execute_sql_success(mocked_sql):
    mocked_cursor = mock.Mock(spec=Cursor)
    mocked_cursor.connection = mock.Mock(spec=Connection)
    _execute_sql(cursor=mocked_cursor, statement=None, params=None, identifiers=None)


@mock.patch("mi.stream_writer.event_handling._execute_sql")
@given(
    record=builds(RecordParams),
    dimension_types=lists(elements=sampled_from(DIMENSION_TYPES)),
)
def test_insert_mi_record_without_not_null_constraint(
    record: RecordParams, dimension_types: list[Dimension], mocked_execute_sql
):

    responses = MiResponses()

    insert_mi_record(
        record_params=record,
        sql=None,
        cursor=None,
        responses=responses,
        dimension_types=tuple(dimension_types),
    )
    # Initial call succeeds, so only one call
    mocked_execute_sql.call_count == 1


@given(
    record=builds(RecordParams),
    dimension_types=lists(elements=sampled_from(DIMENSION_TYPES)),
)
def test_insert_mi_record_with_not_null_contraint(
    record: RecordParams, dimension_types: list[Dimension]
):
    responses = MiResponses()

    class _IntegrityError(Exception):
        NOT_NULL = "not_null"

        def __init__(self, pgcode: str):
            self.pgcode = pgcode

    error = _IntegrityError(pgcode=_IntegrityError.NOT_NULL)
    # Initial call fails, then n successful calls plus one final successful call
    expected_calls = [error] + ([None] * len(dimension_types)) + [None]

    with mock.patch(
        "mi.stream_writer.event_handling._execute_sql", side_effect=expected_calls
    ) as mocked__execute_sql:
        response = insert_mi_record(
            record_params=record,
            sql=None,
            cursor=None,
            responses=responses,
            dimension_types=tuple(dimension_types),
            integrity_error_type=_IntegrityError,
            not_null_violation=_IntegrityError.NOT_NULL,
        )
        assert mocked__execute_sql.call_count == len(expected_calls)

    assert type(response) is not ErrorResponse, response


@mock.patch("mi.stream_writer.event_handling._execute_sql")
@given(
    record=builds(RecordParams),
    dimension_types=lists(elements=sampled_from(DIMENSION_TYPES)),
)
def test_insert_mi_record_with_any_other_pg_error(
    record: RecordParams, dimension_types: list[Dimension], mocked_execute_sql
):
    class _IntegrityError(Exception):
        NOT_NULL = "not_null"

        def __init__(self, pgcode: str):
            self.pgcode = pgcode

    responses = MiResponses()

    error = _IntegrityError(pgcode="oops")
    mocked_execute_sql.side_effect = [error]

    response = insert_mi_record(
        record_params=record,
        sql=None,
        cursor=None,
        responses=responses,
        dimension_types=tuple(dimension_types),
        integrity_error_type=_IntegrityError,
        not_null_violation=_IntegrityError.NOT_NULL,
    )
    assert type(response) is ErrorResponse

    assert response == ErrorResponse(
        error="",
        error_type="_IntegrityError",
        trace=response.trace,
        function="mi.stream_writer.event_handling.insert_mi_record",
    )


@given(
    pk=from_regex(r"^D#.*"),
    other_keys=dictionaries(keys=text(), values=text()),
)
def test_is_document_pointer_pass(pk: str, other_keys: dict):
    assert is_document_pointer(pk=pk, **other_keys)


@given(pk=from_regex(r"^D#.*"), sk=text())
def test_is_document_pointer_pass_from_dynamodb_record(pk: str, sk: str):
    stream_record = StreamRecord({"Keys": {"pk": {"S": pk}, "sk": {"S": sk}}})
    assert is_document_pointer(**stream_record.keys)


@given(
    pk=from_regex(r"^[a-zA-Z[D]]#.*"),
    other_keys=dictionaries(keys=text(), values=text()),
)
def test_is_document_pointer_fail(pk: str, other_keys: dict):
    assert not is_document_pointer(pk=pk, **other_keys)


@given(pk=from_regex(r"^[a-zA-Z[D]]#.*"), sk=text())
def test_is_document_pointer_fail_from_dynamodb_record(pk: str, sk: str):
    stream_record = StreamRecord({"Keys": {"pk": {"S": pk}, "sk": {"S": sk}}})
    assert not is_document_pointer(**stream_record.keys)
