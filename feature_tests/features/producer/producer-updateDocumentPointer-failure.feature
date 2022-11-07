Feature: Failure scenarios where producer is unable to update a Document Pointer

  Background:
    Given template DOCUMENT:
      """
      {
          "resourceType": "DocumentReference",
          "id": "$custodian|$identifier",
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
          "status": "$status",
          "relatesTo": [
              {
                  "code": "replaces",
                  "target": {
                      "type": "DocumentReference",
                      "identifier": {
                          "value": "$relatesTo"
                      }
                  }
              }
          ]
      }
      """
    And a Document Pointer exists in the system with the below values
      | property    | value                                   |
      | identifier  | 1234567890                              |
      | type        | 736253002                               |
      | custodian   | ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL |
      | subject     | 9278693472                              |
      | contentType | application/pdf                         |
      | status      | current                                 |
      | url         | https://example.org/my-doc.pdf          |

  Scenario: Unable to update a Document Pointer that does not exist
    Given Producer "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL" has permission to update Document Pointers for
      | snomed_code | description                 |
      | 736253002   | "Mental health crisis plan" |
    When Producer "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL" updates a Document Reference "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL|0987654321" from DOCUMENT template
      | property    | value                                   |
      | identifier  | 1234567890                              |
      | status      | current                                 |
      | type        | 736253002                               |
      | custodian   | ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL |
      | subject     | 9278693472                              |
      | contentType | application/pdf                         |
      | url         | https://example.org/different-doc.pdf   |
    Then the operation is unsuccessful
    And the response contains error message "Item could not be found"

  Scenario: Unable to update a Document Pointer when Producer does not have permission
    Given Producer "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL 2" has permission to update Document Pointers for
      | snomed_code | description                 |
      | 736253002   | "Mental health crisis plan" |
    When Producer "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL 2" updates a Document Reference "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL|1234567890" from DOCUMENT template
      | property    | value                                   |
      | identifier  | 1234567890                              |
      | status      | current                                 |
      | type        | 736253002                               |
      | custodian   | ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL |
      | subject     | 9278693472                              |
      | contentType | application/pdf                         |
      | url         | https://example.org/different-doc.pdf   |
    Then the operation is unsuccessful
    And the response contains error message "Item could not be found"

  Scenario: Unable to update the relatesTo immutable property of a DOCUMENT_POINTER
    Given Producer "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL" has permission to update Document Pointers for
      | snomed_code | description                 |
      | 736253002   | "Mental health crisis plan" |
    When Producer "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL" updates a Document Reference "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL|1234567890" from DOCUMENT template
      | property    | value                                   |
      | identifier  | 1234567890                              |
      | status      | current                                 |
      | type        | 736253002                               |
      | custodian   | ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL |
      | subject     | 9278693472                              |
      | contentType | application/pdf                         |
      | relatesTo   | 536941082                               |
    Then the operation is unsuccessful
    And the response contains error message "Trying to update one or more immutable fields"

  Scenario: Unable to update the status immutable property of a DOCUMENT_POINTER
    Given Producer "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL" has permission to update Document Pointers for
      | snomed_code | description                 |
      | 736253002   | "Mental health crisis plan" |
    When Producer "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL" updates a Document Reference "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL|1234567890" from DOCUMENT template
      | property    | value                                   |
      | identifier  | 1234567890                              |
      | status      | deleted                                 |
      | type        | 736253002                               |
      | custodian   | ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL |
      | subject     | 9278693472                              |
      | contentType | application/pdf                         |
    Then the operation is unsuccessful
    And the response contains error message "Trying to update one or more immutable fields"

  Scenario: Unable to update the custodian immutable property of a DOCUMENT_POINTER
    Given Producer "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL" has permission to update Document Pointers for
      | snomed_code | description                 |
      | 736253002   | "Mental health crisis plan" |
    When Producer "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL" updates a Document Reference "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL|1234567890" from DOCUMENT template
      | property    | value                                     |
      | identifier  | 1234567890                                |
      | status      | current                                   |
      | type        | 736253002                                 |
      | custodian   | ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL 2 |
      | subject     | 9278693472                                |
      | contentType | application/pdf                           |
    Then the operation is unsuccessful
    And the response contains error message "Trying to update one or more immutable fields"
