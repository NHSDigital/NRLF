import pytest

from nrlf.core.codes import NRLResponseConcept, SpineErrorConcept, _CodeableConcept


def test_from_code_known_code():
    # Arrange
    code = "ABC"
    expected_text = "ABC Text"
    _CodeableConcept._TEXT_MAP = {"ABC": expected_text}
    _CodeableConcept._SYSTEM = "http://example.com"

    # Act
    result = _CodeableConcept.from_code(code)

    # Assert
    assert result.coding is not None
    assert len(result.coding) == 1

    assert result.coding[0].system == _CodeableConcept._SYSTEM
    assert result.coding[0].code == code
    assert result.coding[0].display == expected_text
    assert result.text == expected_text


def test_from_code_unknown_code():
    # Arrange
    code = "XYZ"
    _CodeableConcept._TEXT_MAP = {"ABC": "ABC Text"}
    _CodeableConcept._SYSTEM = "http://example.com"

    # Act & Assert
    with pytest.raises(ValueError, match="Unknown code: XYZ"):
        _CodeableConcept.from_code(code)


@pytest.mark.parametrize(
    ("code", "expected_text"),
    [
        ("RESOURCE_CREATED", "Resource created"),
        ("RESOURCE_SUPERSEDED", "Resource created and resource(s) deleted"),
        ("RESOURCE_UPDATED", "Resource updated"),
        ("RESOURCE_DELETED", "Resource deleted"),
    ],
)
def test_nrl_response_concept_from_code(code, expected_text):
    # Act
    result = NRLResponseConcept.from_code(code)

    # Assert
    assert result.coding is not None
    assert len(result.coding) == 1
    assert result.coding[0].system == NRLResponseConcept._SYSTEM
    assert result.coding[0].code == code
    assert result.coding[0].display == expected_text
    assert result.text == expected_text


@pytest.mark.parametrize(
    ("code", "expected_text"),
    [
        ("NO_RECORD_FOUND", "No record found"),
        ("INVALID_NHS_NUMBER", "Invalid NHS number"),
        ("INVALID_CODE_SYSTEM", "Invalid code system"),
        ("INTERNAL_SERVER_ERROR", "Unexpected internal server error"),
        ("BAD_REQUEST", "Bad request"),
        ("AUTHOR_CREDENTIALS_ERROR", "Author credentials error"),
        ("DUPLICATE_REJECTED", "Create would lead to creation of a duplicate resource"),
    ],
)
def test_spine_error_concept_from_code(code, expected_text):
    # Act
    result = SpineErrorConcept.from_code(code)

    # Assert
    assert result.coding is not None
    assert len(result.coding) == 1
    assert result.coding[0].system == SpineErrorConcept._SYSTEM
    assert result.coding[0].code == code
    assert result.coding[0].display == expected_text
    assert result.text == expected_text
