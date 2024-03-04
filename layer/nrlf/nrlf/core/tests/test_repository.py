import pytest

from feature_tests.common.repository import FeatureTestRepository as Repository
from feature_tests.common.utils import get_environment_prefix
from helpers.aws_session import new_aws_session
from nrlf.core.dynamodb_types import DynamoDbStringType
from nrlf.core.model import ConsumerRequestParams, DynamoDbModel
from nrlf.core.repository import (
    PAGE_ITEM_LIMIT,
    _decode,
    _encode,
    _expression_attribute_names,
    _expression_attribute_values,
    _filter_expression,
    _key_and_filter_clause,
    _key_condition_expression,
    custodian_filter,
    type_filter,
)


@pytest.mark.parametrize(
    ["input", "expected"],
    [
        [
            {"alpha": 123, "bravo": ["a", "b", "c"]},
            "#alpha = :alpha AND #bravo in (:bravo_1, :bravo_2, :bravo_3)",
        ]
    ],
)
def test_filter_expression(input: dict, expected: str):
    actual = _filter_expression(input)
    assert actual == expected


@pytest.mark.parametrize(
    ["input", "expected"],
    [
        [
            {"alpha": 123, "bravo": ["a", "b", "c"]},
            {"#alpha": "alpha", "#bravo": "bravo"},
        ]
    ],
)
def test_filter_attribute_names(input: dict, expected: dict):
    actual = _expression_attribute_names(input)
    assert actual == expected


@pytest.mark.parametrize(
    ["input", "expected"],
    [
        [
            {"alpha": 123, "bravo": ["a", "b", "c"]},
            {
                ":alpha": {"N": 123},
                ":bravo_1": {"S": "a"},
                ":bravo_2": {"S": "b"},
                ":bravo_3": {"S": "c"},
            },
        ],
        [{"pk": "123"}, {":pk": {"S": "123"}}],
    ],
)
def test_attribute_values(input: dict, expected: dict):
    actual = _expression_attribute_values(input)
    assert actual == expected


@pytest.mark.parametrize(
    ["key", "filter", "expected"],
    [
        [
            {"pk": "D#0", "sk": "D#0"},
            {"type": []},
            {
                "KeyConditionExpression": "pk = :pk AND sk = :sk",
                "FilterExpression": "#type in ()",
                "ExpressionAttributeNames": {"#type": "type"},
                "ExpressionAttributeValues": {
                    ":pk": {"S": "D#0"},
                    ":sk": {"S": "D#0"},
                },
            },
        ],
        [
            {"pk": "D#0", "sk": "D#0"},
            None,
            {
                "KeyConditionExpression": "pk = :pk AND sk = :sk",
                "ExpressionAttributeValues": {":pk": {"S": "D#0"}, ":sk": {"S": "D#0"}},
            },
        ],
        [
            {"pk": "D#0", "sk": "D#0"},
            {"alpha": 123, "bravo": ["a", "b", "c"]},
            {
                "KeyConditionExpression": "pk = :pk AND sk = :sk",
                "FilterExpression": "#alpha = :alpha AND #bravo in (:bravo_1, :bravo_2, :bravo_3)",
                "ExpressionAttributeNames": {
                    "#alpha": "alpha",
                    "#bravo": "bravo",
                },
                "ExpressionAttributeValues": {
                    ":pk": {"S": "D#0"},
                    ":sk": {"S": "D#0"},
                    ":alpha": {"N": 123},
                    ":bravo_1": {"S": "a"},
                    ":bravo_2": {"S": "b"},
                    ":bravo_3": {"S": "c"},
                },
            },
        ],
        [
            {"pk": "D#0", "sk": "D#0"},
            {},
            {
                "KeyConditionExpression": "pk = :pk AND sk = :sk",
                "ExpressionAttributeValues": {":pk": {"S": "D#0"}, ":sk": {"S": "D#0"}},
            },
        ],
        [
            {"pk": "D#0", "sk": "D#0"},
            {"nhs_number": None},
            {
                "KeyConditionExpression": "pk = :pk AND sk = :sk",
                "ExpressionAttributeValues": {":pk": {"S": "D#0"}, ":sk": {"S": "D#0"}},
            },
        ],
    ],
)
def test_key_and_filter_clause(key: dict, filter: dict, expected: dict):
    actual = _key_and_filter_clause(key, filter)
    assert actual == expected


@pytest.mark.parametrize(
    ["input", "expected"],
    [
        [{"pk": "123"}, "pk = :pk"],
        [{"pk": "123", "sk": "456"}, "pk = :pk AND sk = :sk"],
        [{"pk": "123", "sk": None}, "pk = :pk"],
    ],
)
def test_key_condition_expression(input: dict, expected: str):
    actual = _key_condition_expression(input)
    assert actual == expected


@pytest.mark.parametrize(
    ["input", "expected"],
    [
        [1, {"N": 1}],
        ["1", {"S": "1"}],
        [True, {"B": True}],
        [None, {"NULL": True}],
        [{}, {"M": {}}],
        [{"foo": {"bar": 1}}, {"M": {"foo": {"M": {"bar": {"N": 1}}}}}],
    ],
)
def test_encode(input: any, expected: str):
    actual = _encode(input)
    assert actual == expected


@pytest.mark.parametrize(
    ["input", "expected"],
    [
        [{"NULL": True}, None],
        [{"B": False}, False],
        [{"B": 0}, False],
        [{"B": True}, True],
        [{"B": 1}, True],
        [{"S": "Something"}, "Something"],
        [{"N": 1.9}, 1.9],
        [{"N": 3}, 3],
        [{"N": "42"}, 42],
        [{"M": {}}, {}],
        [{"M": {"foo": {"S": "a"}, "bar": {"N": 999}}}, {"foo": "a", "bar": 999}],
        [{"M": {"foo": {"M": {"bar": {"N": 666}}}}}, {"foo": {"bar": 666}}],
        [{"L": []}, []],
        [{"L": [{"N": 123}, {"S": "a"}]}, [123, "a"]],
    ],
)
def test_decode(input: dict, expected: any):
    actual = _decode(input)
    assert actual == expected


def test_custodian_filter():
    queryStringParameters = {
        "subject:identifier": "https://fhir.nhs.uk/Id/nhs-number|3495456481",
        "custodian:identifier": "https://fhir.nhs.uk/Id/ods-organization-code|RY26A",
    }
    request_params = ConsumerRequestParams(**queryStringParameters or {})

    actual = custodian_filter(request_params.custodian_identifier)
    expected = "RY26A"
    assert actual == expected


def test_custodian_filter_none():
    queryStringParameters = {
        "subject:identifier": "https://fhir.nhs.uk/Id/nhs-number|3495456481",
        "custodian:identifier": None,
    }
    request_params = ConsumerRequestParams(**queryStringParameters or {})

    actual = custodian_filter(request_params.custodian_identifier)
    expected = None
    assert actual == expected


def test_type_filter():
    queryStringParameters = {
        "subject:identifier": "https://fhir.nhs.uk/Id/nhs-number|3495456481",
        "type": "http://snomed.info/sct|861421000000109",
    }

    pointer_types = [
        "http://snomed.info/sct|861421000000109",
        "http://snomed.info/sct|861421000000108",
    ]
    request_params = ConsumerRequestParams(**queryStringParameters or {})

    actual = type_filter(request_params.type, pointer_types)
    expected = ["http://snomed.info/sct|861421000000109"]
    assert actual == expected


def test_type_filter_none():
    queryStringParameters = {
        "subject:identifier": "https://fhir.nhs.uk/Id/nhs-number|3495456481",
    }
    pointer_types = [
        "http://snomed.info/sct|861421000000109",
        "http://snomed.info/sct|861421000000108",
    ]
    request_params = ConsumerRequestParams(**queryStringParameters or {})

    actual = type_filter(request_params.type, pointer_types)
    expected = [
        "http://snomed.info/sct|861421000000109",
        "http://snomed.info/sct|861421000000108",
    ]
    assert actual == expected


@pytest.mark.integration
def test_limit():
    class DummyModel(DynamoDbModel):
        pk: DynamoDbStringType
        sk: DynamoDbStringType

        @classmethod
        def kebab(cls) -> str:
            return "document-pointer"

    session = new_aws_session()
    client = session.client("dynamodb")
    environment_prefix = get_environment_prefix(None)
    repository = Repository(
        item_type=DummyModel, client=client, environment_prefix=environment_prefix
    )
    repository.delete_all()

    repository.upsert_many(
        [
            DummyModel(
                pk=DynamoDbStringType(root="DUMMY"),
                sk=DynamoDbStringType(root=f"DUMMY#{i}"),
            )
            for i in range(50)
        ]
    )

    assert len(repository.query("DUMMY", limit=10).items) == 10
    assert len(repository.query("DUMMY").items) == PAGE_ITEM_LIMIT
    assert len(repository.query("DUMMY", limit=100).items) == 50
    assert len(repository.query("DUMMY", limit=None).items) == 50
    assert len(repository.query("DUMMY", limit=-1).items) == 50
