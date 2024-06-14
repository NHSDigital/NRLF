# ID not in path
# Invalid producer ID in ID
Feature: Producer - deleteDocumentReference - Failure Scenarios

  Scenario: Cannot delete another organisation's Document Pointer
    Given the application 'DataShare' (ID 'z00z-y11y-x22x') is registered to access the API
    And the organisation 'DK94' is authorised to access pointer types:
      | system                 | value           |
      | http://snomed.info/sct | 736253002       |
      | http://snomed.info/sct | 861421000000109 |
    And a DocumentReference resource exists with values:
      | property    | value                              |
      | id          | OC84-111-DeleteTest-NotYourPointer |
      | subject     | 9278693472                         |
      | status      | current                            |
      | type        | 861421000000109                    |
      | category    | 734163000                          |
      | contentType | application/pdf                    |
      | url         | https://example.org/my-doc.pdf     |
      | custodian   | OC84                               |
      | author      | N64                                |
    When producer 'DK94' requests to delete DocumentReference with id 'OC84-111-DeleteTest-NotYourPointer'
    Then the response status code is 403
    And the response is an OperationOutcome with 1 issue
    And the OperationOutcome contains the issue:
      """
      {
        "severity": "error",
        "code": "forbidden",
        "details": {
          "coding": [
            {
              "system": "https://fhir.nhs.uk/ValueSet/Spine-ErrorOrWarningCode-1",
              "code": "AUTHOR_CREDENTIALS_ERROR",
              "display": "Author credentials error"
            }
          ]
        },
        "diagnostics": "The requested DocumentReference cannot be deleted because it belongs to another organisation"
      }
      """

# Credentials - none provided
# Credentials - missing pointer type
# Invalid ID format (X26|something-)
