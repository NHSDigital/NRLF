import pytest

SEED = "3FA23470BA123EF1"  # pragma: allowlist secret
LOGICAL_ID = "4d825495-3ada-45ce-a846-f689ec6af27e"
TOKENISED_ID = "4d825495-3ada-45ce-a846-f689ec6af27e-58445655354f5056504d"
NHS_NUMBER = "9541179975"


@pytest.mark.legacy
def test_encrypt():
    from nrlf.legacy.tokeniser import encode_logical_id

    assert (
        encode_logical_id(logical_id=LOGICAL_ID, nhs_number=NHS_NUMBER, seed=SEED)
        == TOKENISED_ID
    )


@pytest.mark.legacy
def test_decrypt():
    from nrlf.legacy.tokeniser import decode_tokenised_id

    assert decode_tokenised_id(tokenised_id=TOKENISED_ID, seed=SEED) == (
        LOGICAL_ID,
        NHS_NUMBER,
    )
