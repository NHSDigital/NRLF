import json
from logging import getLogger
from unittest import mock

from aws_lambda_powertools.utilities.parser.models import APIGatewayProxyEventModel
from lambda_pipeline.types import PipelineData
from lambda_utils.tests.unit.utils import make_aws_event
from nrlf.core.constants import ID_SEPARATOR
from nrlf.core.model import DocumentPointer
from nrlf.producer.fhir.r4.tests.test_producer_nrlf_model import read_test_data

from api.producer.createDocumentReference.src.v1.handler import parse_request_body


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
            "id": {
                "S": f"ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL{ID_SEPARATOR}1234567890"
            },
            "nhs_number": {"S": "9278693472"},
            "producer_id": {"S": "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL"},
            "custodian": {"S": "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL"},
            "source": {"S": "NRLF"},
            "type": {"S": "https://snomed.info/ict|736253002"},
            "updated_on": {"NULL": True},
            "version": {"N": "1"},
        }
    )
    pipeline_data = parse_request_body(
        PipelineData(), {}, event, {}, getLogger(__name__)
    )

    assert pipeline_data["core_model"].dict() == expected_output.dict()
