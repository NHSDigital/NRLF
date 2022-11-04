Feature: Failure Scenarios where producer unable to supersede Document Pointers

  Background:
    Given template DOCUMENT
      """
      {
          "resourceType": "DocumentReference",
          "id": "$identifier",
          "custodian": {
              "identifier": {
                  "system": "https://fhir.nhs.uk/Id/accredited-system-id",
                  "value": "$custodian"
              }
          },
          "subject": {
              "identifier": {
                  "system": "https://fhir.nhs.uk/Id/nhs-number",
                  "value": "$subject"
              }
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
          "status": "current",
          "relatesTo": [
              {
                  "code": "replaces",
                  "target": {
                      "type": "DocumentReference",
                      "identifier": {
                          "value": "$target"
                      }
                  }
              }
          ]
      }
      """

  Scenario: Producer does not have permission to create the supersede Document Pointer
    Given a Document Pointer exists in the system with the below values
      | property    | value                                               |
      | identifier  | ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL\|1234567890 |
      | type        | 736253002                                           |
      | custodian   | ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL             |
      | subject     | 9278693472                                          |
      | contentType | application/pdf                                     |
      | url         | https://example.org/my-doc.pdf                      |
    And Producer "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL" has permission to create Document Pointers for
      | snomed_code | description               |
      | 736253002   | Mental health crisis plan |
    When Producer "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL" creates a Document Reference from DOCUMENT template
      | property    | value                                               |
      | identifier  | ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL\|1234567892 |
      | target      | ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL\|1234567890 |
      | type        | 734163000                                           |
      | custodian   | ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL             |
      | subject     | 9278693472                                          |
      | contentType | application/pdf                                     |
      | url         | https://example.org/my-doc.pdf                      |
    Then the operation is unsuccessful
    And the response contains error message "Required permission to create a document pointer are missing"

  Scenario: Producer does not have permission to delete the superseded Document Pointer
    Given a Document Pointer exists in the system with the below values
      | property    | value                             |
      | identifier  | AARON COURT MENTAL NH\|1234567890 |
      | type        | 736253002                         |
      | custodian   | AARON COURT MENTAL NH             |
      | subject     | 9278693472                        |
      | contentType | application/pdf                   |
      | url         | https://example.org/my-doc.pdf    |
    And Producer "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL" has permission to create Document Pointers for
      | snomed_code | description |
      | 734163000   | Care plan   |
    When Producer "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL" creates a Document Reference from DOCUMENT template
      | property    | value                                               |
      | identifier  | ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL\|1234567892 |
      | target      | AARON COURT MENTAL NH\|1234567890                   |
      | type        | 734163000                                           |
      | custodian   | ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL             |
      | subject     | 9278693472                                          |
      | contentType | application/pdf                                     |
      | url         | https://example.org/my-doc.pdf                      |
    Then the operation is unsuccessful
    And the response contains error message "Required permission to delete a document pointer are missing"

  Scenario: The superseded Document Pointer does not exist                |
    Given Producer "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL" has permission to create Document Pointers for
      | snomed_code | description               |
      | 736253002   | Mental health crisis plan |
    When Producer "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL" creates a Document Reference from DOCUMENT template
      | property    | value                                               |
      | identifier  | ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL\|1234567892 |
      | target      | ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL\|1234567890 |
      | type        | 736253002                                           |
      | custodian   | ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL             |
      | subject     | 9278693472                                          |
      | contentType | application/pdf                                     |
      | url         | https://example.org/my-doc.pdf                      |
    Then the operation is unsuccessful
    And the response contains error message "Condition check failed - Supersede ID mismatch"
