Feature: Producer - upsertDocumentReference - Failure Scenarios

  Scenario: Invalid category for type
    Given the application 'DataShare' (ID 'z00z-y11y-x22x') is registered to access the API
    And the organisation 'X26' is authorised to access pointer types:
      | system                 | value            |
      | http://snomed.info/sct | 1363501000000100 |
      | http://snomed.info/sct | 736253002        |
    When producer 'X26' upserts a DocumentReference with values:
      | property  | value                          |
      | id        | X26-testid-upsert-0001-0001    |
      | subject   | 9999999999                     |
      | status    | current                        |
      | type      | 736253002                      |
      | category  | 1102421000000108               |
      | custodian | X26                            |
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
        "diagnostics": "The Category code of the provided document 'http://snomed.info/sct|1102421000000108' must match the allowed category for pointer type 'http://snomed.info/sct|736253002' with a category value of 'http://snomed.info/sct|734163000'",
        "expression": [
        "category.coding[0].code"
        ]
      }
      """
