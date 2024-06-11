# Invalid document reference - structure
# Invalid document reference - required fields missing
# Invalid document reference - extra fields provided
# Invalid document reference - missing custodian identifier
# Invalid document reference - missing subject identifier
# Invalid document reference - invalid custodian system
# Invalid document reference - invalid subject system
# Invalid document reference - invalid relatesTo code
# Invalid document reference - invalid relatesTo target
# Invalid document reference - multiple type.coding
# Invalid document reference - invalid custodian suffix
Feature: Producer - createDocumentReference - Failure Scenarios

  Scenario: Producer and custodian ODS mismatch
    Given the application 'DataShare' (ID 'z00z-y11y-x22x') is registered to access the API
    And the organisation 'ANGY1' is authorised to access pointer types:
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    When producer 'ANGY1' creates a DocumentReference with values:
      | property  | value                          |
      | subject   | 9999999999                     |
      | status    | current                        |
      | type      | 736253002                      |
      | category  | 734163000                      |
      | custodian | N0TANGY                        |
      | author    | HAR1                           |
      | url       | https://example.org/my-doc.pdf |
    Then the response status code is 400
    And the response is an OperationOutcome with 1 issue
    And the OperationOutcome contains the issue:
      """
      {
        "severity": "error",
        "code": "invalid",
        "details": {
            "coding": [
            {
                "system": "https://fhir.nhs.uk/ValueSet/Spine-ErrorOrWarningCode-1",
                "code": "BAD_REQUEST",
                "display": "Bad request"
            }
            ]
        },
        "diagnostics": "The custodian of the provided DocumentReference does not match the expected ODS code for this organisation",
        "expression": [
            "custodian.identifier.value"
        ]
      }
      """

  Scenario: Invalid NHS number (correct length but not valid)
    Given the application 'DataShare' (ID 'z00z-y11y-x22x') is registered to access the API
    And the organisation 'ANGY1' is authorised to access pointer types:
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    When producer 'ANGY1' creates a DocumentReference with values:
      | property  | value                          |
      | subject   | 1234567890                     |
      | status    | current                        |
      | type      | 736253002                      |
      | category  | 734163000                      |
      | custodian | ANGY1                          |
      | author    | HAR1                           |
      | url       | https://example.org/my-doc.pdf |
    # NRL-765 known bug: this response is not handled properly, currently gives a 500
    # Then the response status code is 400
    Then the response is an OperationOutcome with 1 issue

# And the OperationOutcome contains the issue:
# """
# {
# "severity": "error",
# "code": "informational",
# "details": {
# "coding": [
# {
# "system": "https://fhir.nhs.uk/ValueSet/Spine-ErrorOrWarningCode-1",
# "code": "BAD_REQUEST",
# "display": "Bad request"
# }
# ]
# },
# "diagnostics": "Invalid NHS number"
# }
# """
# Invalid document reference - invalid producer ID
# Invalid document reference - invalid custodian ID
# Invalid document reference - invalid relatesTo target
# Invalid document reference - invalid producer ID in relatesTo target
# Invalid document reference - superseded document reference not found
# Invalid document reference - superseded document reference NHS number mismatch
# Invalid document reference - superseded document reference pointer type mismatch
# Credentials - no pointer types allowed
# Credentials - missing pointer type for create
# Invalid document reference - missing type.coding
# Invalid document reference - empty content[0].attachment.url
# Invalid document reference - create another producers document
# Duplicate Document Reference - returns 409
# Invalid document reference - bad JSON
# Invalid document reference - duplicate keys
# Invalid document reference - duplicate relatesTo targets in URL
# Invalid document reference - supersede with duplicate error
# Invalid document reference - missing audit date when permission to set audit date
# Invalid document reference - SSP URL?
