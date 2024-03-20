import json
from copy import deepcopy
from logging import getLogger
from unittest import mock

from lambda_pipeline.types import PipelineData
from lambda_utils.tests.unit.utils import make_aws_event

from api.producer.createDocumentReference.src.v1.handler import (
    _set_create_date_fields,
    parse_request_body,
)
from nrlf.core.constants import ID_SEPARATOR
from nrlf.core.model import APIGatewayProxyEventModel, DocumentPointer
from nrlf.core.validators import json_loads
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
            "id": {"S": f"Y05868{ID_SEPARATOR}1234567890"},
            "nhs_number": {"S": "9278693472"},
            "producer_id": {"S": "Y05868"},
            "custodian": {"S": "Y05868"},
            "source": {"S": "NRLF"},
            "type": {"S": "http://snomed.info/sct|736253002"},
            "updated_on": {"NULL": True},
            "version": {"N": "1"},
        }
    )
    pipeline_data = parse_request_body(
        PipelineData(), {}, event, {}, getLogger(__name__)
    )

    assert pipeline_data["core_model"].dict() == expected_output.dict()


@mock.patch(
    "api.producer.createDocumentReference.src.v1.handler.make_timestamp",
    return_value="2024-03-15T12:34:56.789Z",
)
def test_set_create_date_fields_when_no_dates_in_ref(mock__make_timestamp):
    test_data = read_test_data("nrlf")
    pointer = DocumentPointer(
        **{
            "created_on": {"S": "2022-10-25T15:47:49.732Z"},
            "document": {"S": json.dumps(test_data)},
            "id": {"S": f"Y05868{ID_SEPARATOR}1234567890"},
            "nhs_number": {"S": "9278693472"},
            "producer_id": {"S": "Y05868"},
            "custodian": {"S": "Y05868"},
            "source": {"S": "NRLF"},
            "type": {"S": "http://snomed.info/sct|736253002"},
            "updated_on": {"NULL": True},
            "version": {"N": "1"},
        }
    )
    expected_timestamp = mock__make_timestamp()
    expected_fhir_model = deepcopy(
        {
            **test_data,
            **{"meta": {"lastUpdated": expected_timestamp}, "date": expected_timestamp},
        }
    )

    result = _set_create_date_fields(pointer)

    assert result.updated_on.dict() == {"NULL": True}
    assert json_loads(result.document.__root__) == expected_fhir_model


@mock.patch(
    "api.producer.createDocumentReference.src.v1.handler.make_timestamp",
    return_value="2024-03-15T12:34:56.789Z",
)
def test_set_create_date_fields_when_date_in_ref(mock__make_timestamp):
    test_data = read_test_data("nrlf")
    test_data["date"] = "2022-10-25T09:54:32.101Z"
    pointer = DocumentPointer(
        **{
            "created_on": {"S": "2022-10-25T15:47:49.732Z"},
            "document": {"S": json.dumps(test_data)},
            "id": {"S": f"Y05868{ID_SEPARATOR}1234567890"},
            "nhs_number": {"S": "9278693472"},
            "producer_id": {"S": "Y05868"},
            "custodian": {"S": "Y05868"},
            "source": {"S": "NRLF"},
            "type": {"S": "http://snomed.info/sct|736253002"},
            "updated_on": {"NULL": True},
            "version": {"N": "1"},
        }
    )
    expected_timestamp = mock__make_timestamp()
    expected_fhir_model = deepcopy(
        {**test_data, **{"meta": {"lastUpdated": expected_timestamp}}}
    )
    expected_fhir_model["date"] = expected_timestamp

    result = _set_create_date_fields(pointer)

    assert result.updated_on.dict() == {"NULL": True}
    assert json_loads(result.document.__root__) == expected_fhir_model


@mock.patch(
    "api.producer.createDocumentReference.src.v1.handler.make_timestamp",
    return_value="2024-03-15T12:34:56.789Z",
)
def test_set_create_date_fields_when_date_and_lastupdated_in_ref(mock__make_timestamp):
    test_data = read_test_data("nrlf")
    test_data["date"] = "2022-10-25T09:54:32.101Z"
    test_data["meta"] = {"lastUpdated": "2022-10-25T09:54:32.101Z"}
    pointer = DocumentPointer(
        **{
            "created_on": {"S": "2022-10-25T15:47:49.732Z"},
            "document": {"S": json.dumps(test_data)},
            "id": {"S": f"Y05868{ID_SEPARATOR}1234567890"},
            "nhs_number": {"S": "9278693472"},
            "producer_id": {"S": "Y05868"},
            "custodian": {"S": "Y05868"},
            "source": {"S": "NRLF"},
            "type": {"S": "http://snomed.info/sct|736253002"},
            "updated_on": {"NULL": True},
            "version": {"N": "1"},
        }
    )
    expected_timestamp = mock__make_timestamp()
    expected_fhir_model = deepcopy(test_data)
    expected_fhir_model["date"] = expected_timestamp
    expected_fhir_model["meta"]["lastUpdated"] = expected_timestamp

    result = _set_create_date_fields(pointer)

    assert result.updated_on.dict() == {"NULL": True}

    document = json_loads(result.document.__root__)
    assert document["date"] == expected_timestamp
    assert document["meta"]["lastUpdated"] == expected_timestamp
