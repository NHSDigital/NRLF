# Invalid target logical ID (wrong org prefix)
# Invalid target logical ID (owned by this org, but pointer already exists)
# Other edge cases will be same as create(POST)
Feature: Producer - upsertDocumentReference - Success Scenarios

  Scenario: Successfully create a Document Pointer with a chosen logical ID (care plan)
    Given the application 'DataShare' (ID 'z00z-y11y-x22x') is registered to access the API
    And the organisation 'ANGY1' is authorised to access pointer types:
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    When producer 'ANGY1' upserts a DocumentReference with values:
      | property  | value                          |
      | id        | ANGY1-testid-upsert-0001-0001  |
      | subject   | 9278693472                     |
      | status    | current                        |
      | type      | 736253002                      |
      | category  | 734163000                      |
      | custodian | ANGY1                          |
      | author    | HAR1                           |
      | url       | https://example.org/my-doc.pdf |
    Then the response status code is 201
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
              "code": "RESOURCE_CREATED",
              "display": "Resource created"
            }
          ]
        },
        "diagnostics": "The document has been created"
      }
      """
    And the Document Reference 'ANGY1-testid-upsert-0001-0001' exists with values:
      | property  | value                          |
      | id        | ANGY1-testid-upsert-0001-0001  |
      | subject   | 9278693472                     |
      | status    | current                        |
      | type      | 736253002                      |
      | category  | 734163000                      |
      | custodian | ANGY1                          |
      | author    | HAR1                           |
      | url       | https://example.org/my-doc.pdf |
