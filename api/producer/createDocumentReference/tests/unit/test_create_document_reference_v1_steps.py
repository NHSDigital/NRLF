import json
from unittest import mock

from aws_lambda_powertools.utilities.parser.models import APIGatewayProxyEventModel
from lambda_pipeline.types import PipelineData
from lambda_utils.tests.unit.utils import make_aws_event
from nrlf.producer.fhir.r4.tests.test_producer_nrlf_model import read_test_data

from api.producer.createDocumentReference.src.v1.handler import parse_request_body


@mock.patch(
    "nrlf.core.transform.make_timestamp", return_value="2022-10-25T15:47:49.732Z"
)
def test_parse_request_body_to_core_model(mock__make_timestamp):
    event = APIGatewayProxyEventModel(
        **make_aws_event(body=json.dumps(read_test_data("nrlf")))
    )
    expected_output = {
        "created_on": {"S": "2022-10-25T15:47:49.732Z"},
        "document": {
            "S": '{"resourceType": "DocumentReference", "masterIdentifier": {"value": "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL|1234567890"}, "custodian": {"system": "https://fhir.nhs.uk/Id/accredited-system-id", "id": "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL"}, "subject": {"system": "https://fhir.nhs.uk/Id/nhs-number", "id": "9278693472"}, "type": {"coding": [{"system": "https://snomed.info/ict", "code": "736253002"}]}, "content": [{"attachment": {"contentType": "application/pdf", "url": "https://example.org/my-doc.pdf"}}], "status": "current"}'
        },
        "id": {"S": "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL|1234567890"},
        "nhs_number": {"S": "9278693472"},
        "producer_id": {"S": "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL"},
        "source": {"S": "NRLF"},
        "type": {"S": "https://snomed.info/ict|736253002"},
        "updated_on": {"NULL": True},
        "version": {"N": "1"},
    }
    pipeline_data = parse_request_body(PipelineData(), {}, event, {})
    assert pipeline_data["core_model"].dict() == expected_output
