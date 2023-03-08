Feature: Producer Search Success scenarios

  Background:
    Given template DOCUMENT
      """
      {
        "resourceType": "DocumentReference",
        "id": "$custodian-$identifier",
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
              "system": "http://snomed.info/sct",
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
    Given Producer "Aaron Court Mental Health NH" (Organisation ID "8FW23") is requesting to search Document Pointers
    And Producer "Aaron Court Mental Health NH" is registered in the system for application "DataShare" (ID "z00z-y11y-x22x") with pointer types
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    And a Document Pointer exists in the system with the below values for DOCUMENT template
      | property    | value                          |
      | identifier  | 1114567890                     |
      | type        | 736253002                      |
      | custodian   | 8FW23                          |
      | subject     | 9278693472                     |
      | contentType | application/pdf                |
      | url         | https://example.org/my-doc.pdf |
    When Producer "Aaron Court Mental Health NH" searches for Document References with query parameters:
      | property           | value                                         |
      | subject.identifier | https://fhir.nhs.uk/Id/nhs-number\|9278693472 |
    Then the operation is successful
    And the response is a Bundle with 1 entries
    And the Bundle contains an Entry with the below values for DOCUMENT template
      | property    | value                          |
      | identifier  | 1114567890                     |
      | type        | 736253002                      |
      | custodian   | 8FW23                          |
      | subject     | 9278693472                     |
      | contentType | application/pdf                |
      | url         | https://example.org/my-doc.pdf |

  Scenario: Successfully search for multiple Document Pointers by NHS number
    Given Producer "Aaron Court Mental Health NH" (Organisation ID "8FW23") is requesting to search Document Pointers
    And Producer "Aaron Court Mental Health NH" is registered in the system for application "DataShare" (ID "z00z-y11y-x22x") with pointer types
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    And a Document Pointer exists in the system with the below values for DOCUMENT template
      | property    | value                          |
      | identifier  | 1114567890                     |
      | type        | 736253002                      |
      | custodian   | 8FW23                          |
      | subject     | 9278693472                     |
      | contentType | application/pdf                |
      | url         | https://example.org/my-doc.pdf |
    And a Document Pointer exists in the system with the below values for DOCUMENT template
      | property    | value                            |
      | identifier  | 2224567890                       |
      | type        | 736253002                        |
      | custodian   | 8FW23                            |
      | subject     | 9278693472                       |
      | contentType | application/pdf                  |
      | url         | https://example.org/my-doc-2.pdf |
    And a Document Pointer exists in the system with the below values for DOCUMENT template
      | property    | value                            |
      | identifier  | 3334567890                       |
      | type        | 555553002                        |
      | custodian   | 8FW23                            |
      | subject     | 9278693472                       |
      | contentType | application/pdf                  |
      | url         | https://example.org/my-doc-2.pdf |
    When Producer "Aaron Court Mental Health NH" searches for Document References with query parameters:
      | property           | value                                         |
      | subject.identifier | https://fhir.nhs.uk/Id/nhs-number\|9278693472 |
    Then the operation is successful
    And the response is a Bundle with 2 entries
    And the Bundle contains an Entry with the below values for DOCUMENT template
      | property    | value                          |
      | identifier  | 1114567890                     |
      | type        | 736253002                      |
      | custodian   | 8FW23                          |
      | subject     | 9278693472                     |
      | contentType | application/pdf                |
      | url         | https://example.org/my-doc.pdf |
    And the Bundle contains an Entry with the below values for DOCUMENT template
      | property    | value                            |
      | identifier  | 2224567890                       |
      | type        | 736253002                        |
      | custodian   | 8FW23                            |
      | subject     | 9278693472                       |
      | contentType | application/pdf                  |
      | url         | https://example.org/my-doc-2.pdf |

  Scenario: Empty results when searching for a Document Pointer when the producer has no documents
    Given Producer "Aaron Court Mental Health NH" (Organisation ID "8FW23") is requesting to search Document Pointers
    And Producer "Aaron Court Mental Health NH" is registered in the system for application "DataShare" (ID "z00z-y11y-x22x") with pointer types
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    And a Document Pointer exists in the system with the below values for DOCUMENT template
      | property    | value                          |
      | identifier  | 1114567890                     |
      | type        | 999253002                      |
      | custodian   | VN6DL                          |
      | subject     | 9278693472                     |
      | contentType | application/pdf                |
      | url         | https://example.org/my-doc.pdf |
    When Producer "Aaron Court Mental Health NH" searches for Document References with query parameters:
      | property           | value                                         |
      | subject.identifier | https://fhir.nhs.uk/Id/nhs-number\|9278693472 |
    Then the operation is successful
    And the response is a Bundle with 0 entries

  Scenario: Empty results when searching for a Document Pointer when subject has no documents with requesting producer
    Given Producer "Aaron Court Mental Health NH" (Organisation ID "8FW23") is requesting to search Document Pointers
    And Producer "Aaron Court Mental Health NH" is registered in the system for application "DataShare" (ID "z00z-y11y-x22x") with pointer types
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    And a Document Pointer exists in the system with the below values for DOCUMENT template
      | property    | value                            |
      | identifier  | 1234567891                       |
      | type        | 736253002                        |
      | custodian   | VN6DL                            |
      | subject     | 7736959498                       |
      | contentType | application/pdf                  |
      | url         | https://example.org/my-doc-2.pdf |
    When Producer "Aaron Court Mental Health NH" searches for Document References with query parameters:
      | property           | value                                         |
      | subject.identifier | https://fhir.nhs.uk/Id/nhs-number\|7736959498 |
    Then the operation is successful
    And the response is a Bundle with 0 entries

  Scenario: Empty results when searching for a Document Pointer when provided document type does not match any documents
    Given Producer "Aaron Court Mental Health NH" (Organisation ID "8FW23") is requesting to search Document Pointers
    And Producer "Aaron Court Mental Health NH" is registered in the system for application "DataShare" (ID "z00z-y11y-x22x") with pointer types
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    And a Document Pointer exists in the system with the below values for DOCUMENT template
      | property    | value                          |
      | identifier  | 1234567890                     |
      | type        | 0000000000                     |
      | custodian   | 8FW23                          |
      | subject     | 7736959498                     |
      | contentType | application/pdf                |
      | url         | https://example.org/my-doc.pdf |
    And a Document Pointer exists in the system with the below values for DOCUMENT template
      | property    | value                            |
      | identifier  | 1234567891                       |
      | type        | 0000000000                       |
      | custodian   | 8FW23                            |
      | subject     | 7736959498                       |
      | contentType | application/pdf                  |
      | url         | https://example.org/my-doc-2.pdf |
    When Producer "Aaron Court Mental Health NH" searches for Document References with query parameters:
      | property           | value                                         |
      | subject.identifier | https://fhir.nhs.uk/Id/nhs-number\|7736959498 |
    Then the operation is successful
    And the response is a Bundle with 0 entries

  Scenario: Successfully searches for all documents belonging to the producer when no parameters passed
    Given Producer "Aaron Court Mental Health NH" (Organisation ID "8FW23") is requesting to search Document Pointers
    And Producer "Aaron Court Mental Health NH" is registered in the system for application "DataShare" (ID "z00z-y11y-x22x") with pointer types
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    And a Document Pointer exists in the system with the below values for DOCUMENT template
      | property    | value                          |
      | identifier  | 1114567890                     |
      | type        | 736253002                      |
      | custodian   | 8FW23                          |
      | subject     | 9278693472                     |
      | contentType | application/pdf                |
      | url         | https://example.org/my-doc.pdf |
    And a Document Pointer exists in the system with the below values for DOCUMENT template
      | property    | value                          |
      | identifier  | 1114567890                     |
      | type        | 736253002                      |
      | custodian   | 9QW12                          |
      | subject     | 9278693472                     |
      | contentType | application/pdf                |
      | url         | https://example.org/my-doc.pdf |
    When Producer "Aaron Court Mental Health NH" searches for Document References with query parameters:
      | property | value |
    Then the operation is successful
    And the response is a Bundle with 1 entries
    And the Bundle contains an Entry with the below values for DOCUMENT template
      | property    | value                          |
      | identifier  | 1114567890                     |
      | type        | 736253002                      |
      | custodian   | 8FW23                          |
      | subject     | 9278693472                     |
      | contentType | application/pdf                |
      | url         | https://example.org/my-doc.pdf |

  Scenario: Successfully searches for documents by subject and type for a producer
    Given Producer "Aaron Court Mental Health NH" (Organisation ID "8FW23") is requesting to search Document Pointers
    And Producer "Aaron Court Mental Health NH" is registered in the system for application "DataShare" (ID "z00z-y11y-x22x") with pointer types
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    And a Document Pointer exists in the system with the below values for DOCUMENT template
      | property    | value                          |
      | identifier  | 1114567890                     |
      | type        | 736253002                      |
      | custodian   | 8FW23                          |
      | subject     | 9278693472                     |
      | contentType | application/pdf                |
      | url         | https://example.org/my-doc.pdf |
    And a Document Pointer exists in the system with the below values for DOCUMENT template
      | property    | value                          |
      | identifier  | 1114567890                     |
      | type        | 861421000000109                |
      | custodian   | 9QW12                          |
      | subject     | 9278693472                     |
      | contentType | application/pdf                |
      | url         | https://example.org/my-doc.pdf |
    When Producer "Aaron Court Mental Health NH" searches for Document References with query parameters:
      | property           | value                                         |
      | subject.identifier | https://fhir.nhs.uk/Id/nhs-number\|9278693472 |
      | type.identifier    | http://snomed.info/sct\|736253002             |
    Then the operation is successful
    And the response is a Bundle with 1 entries
    And the Bundle contains an Entry with the below values for DOCUMENT template
      | property    | value                          |
      | identifier  | 1114567890                     |
      | type        | 736253002                      |
      | custodian   | 8FW23                          |
      | subject     | 9278693472                     |
      | contentType | application/pdf                |
      | url         | https://example.org/my-doc.pdf |

  Scenario: Successfully searches for all documents by type for a producer
    Given Producer "Aaron Court Mental Health NH" (Organisation ID "8FW23") is requesting to search Document Pointers
    And Producer "Aaron Court Mental Health NH" is registered in the system for application "DataShare" (ID "z00z-y11y-x22x") with pointer types
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    And a Document Pointer exists in the system with the below values for DOCUMENT template
      | property    | value                          |
      | identifier  | 1114567890                     |
      | type        | 736253002                      |
      | custodian   | 8FW23                          |
      | subject     | 9278693472                     |
      | contentType | application/pdf                |
      | url         | https://example.org/my-doc.pdf |
    And a Document Pointer exists in the system with the below values for DOCUMENT template
      | property    | value                          |
      | identifier  | 1114567890                     |
      | type        | 861421000000109                |
      | custodian   | 9QW12                          |
      | subject     | 9278693472                     |
      | contentType | application/pdf                |
      | url         | https://example.org/my-doc.pdf |
    When Producer "Aaron Court Mental Health NH" searches for Document References with query parameters:
      | property        | value                             |
      | type.identifier | http://snomed.info/sct\|736253002 |
    Then the operation is successful
    And the response is a Bundle with 1 entries
    And the Bundle contains an Entry with the below values for DOCUMENT template
      | property    | value                          |
      | identifier  | 1114567890                     |
      | type        | 736253002                      |
      | custodian   | 8FW23                          |
      | subject     | 9278693472                     |
      | contentType | application/pdf                |
      | url         | https://example.org/my-doc.pdf |

  Scenario: Successfully searches for all documents and provides last evaluated key when above 20 record limit
    Given Producer "Aaron Court Mental Health NH" (Organisation ID "8FW23") is requesting to search Document Pointers
    And Producer "Aaron Court Mental Health NH" is registered in the system for application "DataShare" (ID "z00z-y11y-x22x") with pointer types
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    And 21 Document Pointers exists in the system with the below values for DOCUMENT template
      | property    | value                          |
      | identifier  | 1114567800                     |
      | type        | 736253002                      |
      | custodian   | 8FW23                          |
      | subject     | 9278693472                     |
      | contentType | application/pdf                |
      | url         | https://example.org/my-doc.pdf |
    When Producer "Aaron Court Mental Health NH" searches for Document References with query parameters:
      | property           | value                                         |
      | subject.identifier | https://fhir.nhs.uk/Id/nhs-number\|9278693472 |
    Then the operation is successful
    And the response is a Bundle with 20 entries
    And the Bundle contains an Entry with the below values for DOCUMENT template
      | property    | value                          |
      | identifier  | 1114567800                     |
      | type        | 736253002                      |
      | custodian   | 8FW23                          |
      | subject     | 9278693472                     |
      | contentType | application/pdf                |
      | url         | https://example.org/my-doc.pdf |
    And the Bundle contains a next page token
    When Producer "Aaron Court Mental Health NH" searches for the next page
    Then the operation is successful
    And the response is a Bundle with 1 entries
    And the Bundle contains an Entry with the below values for DOCUMENT template
      | property    | value                          |
      | identifier  | 1114567820                     |
      | type        | 736253002                      |
      | custodian   | 8FW23                          |
      | subject     | 9278693472                     |
      | contentType | application/pdf                |
      | url         | https://example.org/my-doc.pdf |
