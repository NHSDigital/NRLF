import json
from copy import deepcopy
from logging import getLogger
from unittest import mock

import pytest
from aws_lambda_powertools.utilities.parser.models import APIGatewayProxyEventModel
from lambda_pipeline.types import PipelineData
from lambda_utils.tests.unit.utils import make_aws_event

from api.producer.updateDocumentReference.src.v1.handler import (
    _validate_immutable_fields,
    compare_immutable_fields,
    parse_request_body,
)
from nrlf.core.errors import ImmutableFieldViolationError
from nrlf.core.model import DocumentPointer
from nrlf.producer.fhir.r4.tests.test_producer_nrlf_model import read_test_data


@mock.patch(
    "nrlf.core.transform.make_timestamp", return_value="2022-10-25T15:47:49.732Z"
)
def test_parse_request_body_to_core_model(mock__make_timestamp):
    fhir_json = json.dumps(read_test_data("nrlf"))
    event = APIGatewayProxyEventModel(**make_aws_event(body=fhir_json))
    expected_output = DocumentPointer(
        **{
            "created_on": {"S": "2022-10-25T15:47:49.732Z"},
            "document": {"S": fhir_json},
            "id": {"S": "Y05868-1234567890"},
            "nhs_number": {"S": "9278693472"},
            "producer_id": {"S": "Y05868"},
            "custodian": {"S": "Y05868"},
            "source": {"S": "NRLF"},
            "type": {"S": "http://snomed.info/sct|736253002"},
            "updated_on": {"S": "2022-10-25T15:47:49.732Z"},
            "version": {"N": "1"},
        }
    )
    pipeline_data = parse_request_body(
        PipelineData(), {}, event, {}, getLogger(__name__)
    )
    assert pipeline_data["core_model"].dict() == expected_output.dict()


@mock.patch(
    "nrlf.core.transform.make_timestamp", return_value="2022-10-25T15:47:49.732Z"
)
def test_compare_immutable_fields_success(mock__make_timestamp):
    fhir_json = read_test_data("nrlf")

    updated_fhir_json = deepcopy(fhir_json)
    updated_fhir_json["content"][0]["attachment"][
        "url"
    ] = "https://example.org/different_doc.pdf"
    event = APIGatewayProxyEventModel(
        **make_aws_event(body=json.dumps(updated_fhir_json))
    )
    expected_output = DocumentPointer(
        **{
            "created_on": {"S": "2022-10-25T15:47:49.732Z"},
            "document": {"S": json.dumps(updated_fhir_json)},
            "id": {"S": "Y05868-1234567890"},
            "nhs_number": {"S": "9278693472"},
            "producer_id": {"S": "Y05868"},
            "custodian": {"S": "Y05868"},
            "source": {"S": "NRLF"},
            "type": {"S": "http://snomed.info/sct|736253002"},
            "updated_on": {"S": "2022-10-25T15:47:49.732Z"},
            "version": {"N": "1"},
        }
    )
    pipeline_data = parse_request_body(
        PipelineData(), {}, event, {}, getLogger(__name__)
    )
    output = dict(pipeline_data)
    output["original_document"] = json.dumps(fhir_json)
    pipeline_data = compare_immutable_fields(
        PipelineData(output), {}, event, {}, getLogger(__name__)
    )
    assert pipeline_data["core_model"].dict() == expected_output.dict()


@mock.patch(
    "nrlf.core.transform.make_timestamp", return_value="2022-10-25T15:47:49.732Z"
)
def test_compare_immutable_fields_failure(mock__make_timestamp):
    fhir_json = read_test_data("nrlf")

    updated_fhir_json = deepcopy(fhir_json)
    updated_fhir_json["custodian"]["identifier"]["value"] = "Y05868 / MODIFIED"

    with pytest.raises(ImmutableFieldViolationError):
        event = APIGatewayProxyEventModel(
            **make_aws_event(body=json.dumps(updated_fhir_json))
        )

        pipeline_data = parse_request_body(
            PipelineData(), {}, event, {}, getLogger(__name__)
        )
        output = dict(pipeline_data)
        output["original_document"] = json.dumps(fhir_json)
        pipeline_data = compare_immutable_fields(
            PipelineData(output), {}, event, {}, getLogger(__name__)
        )


_IMMUTABLE_FIELDS = {"foo", "bar"}


@pytest.mark.parametrize("field", _IMMUTABLE_FIELDS)
def test__validate_immutable_fields(field):
    a = {_field: f"a{_field}" for _field in _IMMUTABLE_FIELDS}
    b = {field: f"b{field}"}
    with pytest.raises(ImmutableFieldViolationError):
        _validate_immutable_fields(immutable_fields=_IMMUTABLE_FIELDS, a=a, b=b)

    with pytest.raises(ImmutableFieldViolationError):
        _validate_immutable_fields(immutable_fields=_IMMUTABLE_FIELDS, a=b, b=a)
