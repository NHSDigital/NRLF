@local
Feature: Failure scenarios where producer is unable to read a Document Pointer

  Background:
    Given template DOCUMENT
      """
      {
        "resourceType": "DocumentReference",
        "masterIdentifier": {
          "value": "$custodian|$identifier"
        },
        "custodian": {
          "system": "https://fhir.nhs.uk/Id/accredited-system-id",
          "id": "$custodian"
        },
        "subject": {
          "system": "https://fhir.nhs.uk/Id/nhs-number",
          "id": "$subject"
        },
        "type": {
          "coding": [
            {
              "system": "https://snomed.info/ict",
              "code": "$type"
            }
          ]
        },
        "content": [
          {
            "attachment": {
              "contentType": "$contentType",
              "url": "$url"
            }
          }
        ],
        "status": "current"
      }
      """

  Scenario: Producer permissions do not match the Document Pointer type
    Given a Document Pointer exists in the system with the below values
      | property    | value                          |
      | identifier  | 1234567890                     |
      | type        | 736253002                      |
      | custodian   | AARON COURT MENTAL NH          |
      | subject     | 9278693472                     |
      | contentType | application/pdf                |
      | url         | https://example.org/my-doc.pdf |
    And Producer "AARON COURT MENTAL NH" has permission to create Document Pointers for
      | snomed_code | description |
      | 734163000   | Care plan   |
    When "AARON COURT MENTAL NH" reads an existing Document Reference "AARON COURT MENTAL NH|1234567890"
    Then the operation is unsuccessful
    And the response contains error message "Item could not be found"


  Scenario: Request comes from a Producer whose ID does not match the Document Pointer's producer ID
    Given a Document Pointer exists in the system with the below values
      | property    | value                          |
      | identifier  | 1234567890                     |
      | type        | 736253002                      |
      | custodian   | AARON COURT MENTAL NH          |
      | subject     | 9278693472                     |
      | contentType | application/pdf                |
      | url         | https://example.org/my-doc.pdf |
    And Producer "ABUNDANT LIFE CARE LIMITED" has permission to create Document Pointers for
      | snomed_code | description               |
      | 736253002   | Mental health crisis plan |
    When "ABUNDANT LIFE CARE LIMITED" reads an existing Document Reference "AARON COURT MENTAL NH|1234567890"
    Then the operation is unsuccessful
    And the response contains error message "Item could not be found"


  Scenario: The Document Pointer does not exist
    Given Producer "AARON COURT MENTAL NH" has permission to create Document Pointers for
      | snomed_code | description               |
      | 736253002   | Mental health crisis plan |
    When "AARON COURT MENTAL NH" reads an existing Document Reference "AARON COURT MENTAL NH|1234567890"
    Then the operation is unsuccessful
    And the response contains error message "Item could not be found"
