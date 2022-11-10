from nrlf.legacy.tokeniser import decode_tokenised_logical_id, encode_logical_id


def test_encrypt():
    logicalIdSeed = "3FA23470BA123EF1"  # pragma: allowlist secret
    logicalId = "4d825495-3ada-45ce-a846-f689ec6af27e"
    nhsNumber = "9541179975"

    expectedLogicalId = "4d825495-3ada-45ce-a846-f689ec6af27e-58445655354f5056504d"
    result = encode_logical_id(logicalId, logicalIdSeed, nhsNumber)

    assert result == expectedLogicalId


def test_decrypt():
    logicalIdSeed = "3FA23470BA123EF1"  # pragma: allowlist secret

    tokenisedLogicalId = "4d825495-3ada-45ce-a846-f689ec6af27e-58445655354f5056504d"

    expectedIdentifier = "4d825495-3ada-45ce-a846-f689ec6af27e"
    expectedNhsNumber = "9541179975"

    identifier, nhsNumber = decode_tokenised_logical_id(
        tokenisedLogicalId, logicalIdSeed
    )

    assert nhsNumber == expectedNhsNumber
    assert identifier == expectedIdentifier
