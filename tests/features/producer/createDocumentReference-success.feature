Feature: Producer - createDocumentReference - Success Scenarios

  Scenario: Successfully create a Document Pointer (care plan)
    Given the application 'DataShare' (ID 'z00z-y11y-x22x') is registered to access the API
    And the organisation 'ANGY1' is authorised to access pointer types:
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    When producer 'ANGY1' creates a DocumentReference with values:
      | property  | value                          |
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
    And the response has a Location header
    And the Location header starts with '/nrl-producer-api/FHIR/R4/DocumentReference/ANGY1-'
    And the resource in the Location header exists with values:
      | property  | value                          |
      | subject   | 9278693472                     |
      | status    | current                        |
      | type      | 736253002                      |
      | category  | 734163000                      |
      | custodian | ANGY1                          |
      | author    | HAR1                           |
      | url       | https://example.org/my-doc.pdf |

  # Create document reference with custodian suffix
  Scenario: Successfully create a Document Pointer (care plan)
    Given the application 'DataShare' (ID 'z00z-y11y-x22x') is registered to access the API
    And the organisation 'ANGY1.suffix-id-001a' is authorised to access pointer types:
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    When producer 'ANGY1.suffix-id-001a' creates a DocumentReference with values:
      | property  | value                          |
      | subject   | 9278693472                     |
      | status    | current                        |
      | type      | 736253002                      |
      | category  | 734163000                      |
      | custodian | ANGY1.suffix-id-001a           |
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
    And the response has a Location header
    And the Location header starts with '/nrl-producer-api/FHIR/R4/DocumentReference/ANGY1-'
    And the resource in the Location header exists with values:
      | property  | value                          |
      | subject   | 9278693472                     |
      | status    | current                        |
      | type      | 736253002                      |
      | category  | 734163000                      |
      | custodian | ANGY1                          |
      | author    | HAR1                           |
      | url       | https://example.org/my-doc.pdf |

  # Create superseding document reference
  Scenario: Successfully create a Document Pointer that supercedes another
    Given the application 'DataShare' (ID 'z00z-y11y-x22x') is registered to access the API
    And the organisation 'ANGY1' is authorised to access pointer types:
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    And a DocumentReference resource exists with values:
      | property    | value                          |
      | id          | ANGY1-111-SupercedeDocRefTest1 |
      | subject     | 9278693472                     |
      | status      | current                        |
      | type        | 736253002                      |
      | category    | 734163000                      |
      | contentType | application/pdf                |
      | url         | https://example.org/my-doc.pdf |
      | custodian   | ANGY1                          |
    When producer 'ANGY1' creates a DocumentReference with values:
      | property   | value                          |
      | subject    | 9278693472                     |
      | status     | current                        |
      | type       | 736253002                      |
      | category   | 734163000                      |
      | custodian  | ANGY1                          |
      | author     | HAR1                           |
      | url        | https://example.org/newdoc.pdf |
      | supercedes | ANGY1-111-SupercedeDocRefTest1 |
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
    And the response has a Location header
    And the Location header starts with '/nrl-producer-api/FHIR/R4/DocumentReference/ANGY1-'
    And the resource in the Location header exists with values:
      | property  | value                          |
      | subject   | 9278693472                     |
      | status    | current                        |
      | type      | 736253002                      |
      | category  | 734163000                      |
      | custodian | ANGY1                          |
      | author    | HAR1                           |
      | url       | https://example.org/newdoc.pdf |
    And the resource with id 'ANGY1-111-SupercedeDocRefTest1' does not exist

# Create document reference with relatesTo - not code='replaces'
# Create document reference with relatesTo - multiple
# Create of each pointer type
# Create with content and contact details
# Create with contact details only
# Successfully create a Document Pointer with overridden created on date when producer has permission to set audit date
# SSP URL??
