from nrlf.core.model import (
    ConnectionMetadata,
    ConsumerRequestParams,
    CountRequestParams,
    ProducerRequestParams,
)


def test_connection_metadata():
    metadata = ConnectionMetadata.parse_obj(
        {
            "nrl.pointer-types": ["test"],
            "nrl.ods-code": "test",
            "nrl.ods-code-extension": "test",
            "nrl.permissions": ["test"],
            "nrl.app-id": "test-nrl",
            "client_rp_details": {
                "developer.app.name": "test",
                "developer.app.id": "test",
            },
        }
    )

    assert isinstance(metadata, ConnectionMetadata)

    assert metadata.pointer_types == ["test"]
    assert metadata.ods_code == "test"
    assert metadata.ods_code_extension == "test"
    assert metadata.nrl_permissions == ["test"]
    assert metadata.nrl_app_id == "test-nrl"
    assert metadata.client_rp_details.developer_app_name == "test"
    assert metadata.client_rp_details.developer_app_id == "test"
    assert metadata.ods_code_parts == ("test", "test")


def test_producer_request_params():
    params = ProducerRequestParams.parse_obj(
        {
            "subject:identifier": "https://fhir.nhs.uk/Id/nhs-number|9999999999",
            "type": "test-type",
            "next-page-token": "page-token",
        }
    )

    assert isinstance(params, ProducerRequestParams)

    assert params.subject_identifier is not None
    assert (
        params.subject_identifier.root == "https://fhir.nhs.uk/Id/nhs-number|9999999999"
    )

    assert params.type is not None
    assert params.type.root == "test-type"

    assert params.next_page_token is not None
    assert params.next_page_token.root == "page-token"

    assert params.nhs_number == "9999999999"


def test_consumer_request_params():
    params = ConsumerRequestParams.parse_obj(
        {
            "subject:identifier": "https://fhir.nhs.uk/Id/nhs-number|9999999999",
            "custodian:identifier": "https://fhir.nhs.uk/Id/ods-organization-code|test",
            "type": "test-type",
            "next-page-token": "page-token",
        }
    )

    assert isinstance(params, ConsumerRequestParams)

    assert params.subject_identifier is not None
    assert (
        params.subject_identifier.root == "https://fhir.nhs.uk/Id/nhs-number|9999999999"
    )

    assert params.custodian_identifier is not None
    assert (
        params.custodian_identifier.root
        == "https://fhir.nhs.uk/Id/ods-organization-code|test"
    )

    assert params.type is not None
    assert params.type.root == "test-type"

    assert params.next_page_token is not None
    assert params.next_page_token.root == "page-token"

    assert params.nhs_number == "9999999999"


def test_count_request_params():
    params = CountRequestParams.parse_obj(
        {
            "subject:identifier": "https://fhir.nhs.uk/Id/nhs-number|9999999999",
        }
    )

    assert isinstance(params, CountRequestParams)

    assert params.subject_identifier is not None
    assert (
        params.subject_identifier.root == "https://fhir.nhs.uk/Id/nhs-number|9999999999"
    )

    assert params.nhs_number == "9999999999"
