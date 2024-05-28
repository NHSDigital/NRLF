# Delete by pointer ID
Feature: Producer - deleteDocumentReference - Success Scenarios

  Scenario: Successfully delete a Document Pointer by logical ID
    Given the application 'DataShare' (ID 'z00z-y11y-x22x') is registered to access the API
    And the organisation 'DK94' is authorised to access pointer types:
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    And a DocumentReference resource exists with values:
      | property    | value                          |
      | id          | DK94-111-DeleteDocRefTest1     |
      | subject     | 9278693472                     |
      | status      | current                        |
      | type        | 861421000000109                |
      | category    | 734163000                      |
      | contentType | application/pdf                |
      | url         | https://example.org/my-doc.pdf |
      | custodian   | DK94                           |
      | author      | N64                            |
    When producer 'DK94' requests to delete DocumentReference with id 'DK94-111-DeleteDocRefTest1'
    Then the response status code is 200
    And the response is an OperationOutcome with 1 issue
    And the OperationOutcome contains the issue:
      """
      {
        "severity": "information",
        "code": "informational",
        "details": {
          "coding": [
            {
              "system": "https://fhir.nhs.uk/ValueSet/NRL-ResponseCode",
              "code": "RESOURCE_DELETED",
              "display": "Resource deleted"
            }
          ]
        },
        "diagnostics": "The requested DocumentReference has been deleted"
      }
      """
    And the resource with id 'DK94-111-DeleteDocRefTest1' does not exist

  # Delete by pointer ID - URL encoded
  # Delete by pointer ID - not found
  Scenario: Document Pointer specified in delete request does not exist
    Given the application 'DataShare' (ID 'z00z-y11y-x22x') is registered to access the API
    And the organisation 'DK94' is authorised to access pointer types:
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    When producer 'DK94' requests to delete DocumentReference with id 'DK94-000-NoPointerHere'
    Then the response status code is 404
    And the response is an OperationOutcome with 1 issue
    And the OperationOutcome contains the issue:
      """
      {
        "severity": "error",
        "code": "not-found",
        "details": {
          "coding": [
            {
              "system": "https://fhir.nhs.uk/ValueSet/Spine-ErrorOrWarningCode-1",
              "code": "NO_RECORD_FOUND",
              "display": "No record found"
            }
          ]
        },
        "diagnostics": "The requested DocumentReference could not be found"
      }
      """
    And the resource with id 'DK94-000-NoPointerHere' does not exist
