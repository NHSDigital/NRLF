Feature: Basic Success Scenarios where consumer is able to search for Document Pointers

  Background:
    Given template DOCUMENT
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
        "status": "current"
      }
      """

  Scenario: Successfully search for a single Document Pointer by NHS number
    Given a Document Pointer exists in the system with the below values
      | property    | value                          |
      | identifier  | 1114567890                     |
      | type        | 736253002                      |
      | custodian   | AARON COURT MENTAL NH          |
      | subject     | 9278693472                     |
      | contentType | application/pdf                |
      | url         | https://example.org/my-doc.pdf |
    And Consumer "TEST CONSUMER" has permission to search Document Pointers for
      | snomed_code | description               |
      | 736253002   | Mental health crisis plan |
    When "TEST CONSUMER" searches with query parameters:
      | property | value                                         |
      | subject  | https://fhir.nhs.uk/Id/nhs-number\|9278693472 |
    And "TEST CONSUMER" searches with the header values:
      | property | value     |
      | type     | 736253002 |
    Then the consumer search is made
    And the operation is successful
    And 1 document reference was returned
    And the response contains the DOCUMENT template with the below values
      | property    | value                          |
      | identifier  | 1114567890                     |
      | type        | 736253002                      |
      | custodian   | AARON COURT MENTAL NH          |
      | subject     | 9278693472                     |
      | contentType | application/pdf                |
      | url         | https://example.org/my-doc.pdf |

  Scenario: Successfully search for multiple Document Pointers by NHS number
    Given a Document Pointer exists in the system with the below values
      | property    | value                          |
      | identifier  | 1114567890                     |
      | type        | 736253002                      |
      | custodian   | AARON COURT MENTAL NH          |
      | subject     | 9278693472                     |
      | contentType | application/pdf                |
      | url         | https://example.org/my-doc.pdf |
    And a Document Pointer exists in the system with the below values
      | property    | value                            |
      | identifier  | 2224567890                       |
      | type        | 736253002                        |
      | custodian   | LIFE A HEALTHY MENTAL LIFE       |
      | subject     | 9278693472                       |
      | contentType | application/pdf                  |
      | url         | https://example.org/my-doc-2.pdf |
    And a Document Pointer exists in the system with the below values
      | property    | value                            |
      | identifier  | 3334567890                       |
      | type        | 555553002                        |
      | custodian   | A DIFFERENT CUSTODIAN            |
      | subject     | 9278693472                       |
      | contentType | application/pdf                  |
      | url         | https://example.org/my-doc-2.pdf |
    And Consumer "TEST CONSUMER" has permission to search Document Pointers for
      | snomed_code | description               |
      | 736253002   | Mental health crisis plan |
    When "TEST CONSUMER" searches with query parameters:
      | property | value                                         |
      | subject  | https://fhir.nhs.uk/Id/nhs-number\|9278693472 |
    And "TEST CONSUMER" searches with the header values:
      | property | value     |
      | type     | 736253002 |
    Then the consumer search is made
    And the operation is successful
    And 2 document references were returned
    And the response contains the DOCUMENT template with the below values
      | property    | value                          |
      | identifier  | 1114567890                     |
      | type        | 736253002                      |
      | custodian   | AARON COURT MENTAL NH          |
      | subject     | 9278693472                     |
      | contentType | application/pdf                |
      | url         | https://example.org/my-doc.pdf |
    And the response contains the DOCUMENT template with the below values
      | property    | value                            |
      | identifier  | 2224567890                       |
      | type        | 736253002                        |
      | custodian   | LIFE A HEALTHY MENTAL LIFE       |
      | subject     | 9278693472                       |
      | contentType | application/pdf                  |
      | url         | https://example.org/my-doc-2.pdf |

  Scenario: Empty results when searching for a Document Pointer when the consumer cant access existing document type
    Given a Document Pointer exists in the system with the below values
      | property    | value                             |
      | identifier  | 1114567890                        |
      | type        | 999253002                         |
      | custodian   | AMBULANCE PEOPLE TRUST IN THYSELF |
      | subject     | 9278693472                        |
      | contentType | application/pdf                   |
      | url         | https://example.org/my-doc.pdf    |
    And Consumer "TEST CONSUMER" has permission to search Document Pointers for
      | snomed_code | description               |
      | 736253002   | Mental health crisis plan |
    When "TEST CONSUMER" searches with query parameters
      | property | value                                         |
      | subject  | https://fhir.nhs.uk/Id/nhs-number\|9278693472 |
    And "TEST CONSUMER" searches with the header values
      | property | value     |
      | type     | 736253002 |
    Then the consumer search is made
    And the response is an empty bundle

  Scenario: Empty results when searching for a Document Pointer when subject has no documents
    Given Consumer "TEST CONSUMER" has permission to search Document Pointers for
      | snomed_code | description               |
      | 736253002   | Mental health crisis plan |
    When "TEST CONSUMER" searches with query parameters
      | property | value                                         |
      | subject  | https://fhir.nhs.uk/Id/nhs-number\|9278693472 |
    And "TEST CONSUMER" searches with the header values
      | property | value     |
      | type     | 736253002 |
    Then the consumer search is made
    And the response is an empty bundle
