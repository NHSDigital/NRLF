Feature: Consumer Search Success scenarios

  Background:
    Given template DOCUMENT
      """
      {
        "resourceType": "DocumentReference",
        "id": "$custodian-$identifier",
        "custodian": {
          "identifier": {
            "system": "https://fhir.nhs.uk/Id/ods-organization-code",
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
    Given Consumer "Yorkshire Ambulance Service" (Organisation ID "RX898") is requesting to search Document Pointers
    And Consumer "Yorkshire Ambulance Service" is registered in the system for application "DataShare" (ID "z00z-y11y-x22x") with pointer types
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
    When Consumer "Yorkshire Ambulance Service" searches for Document References with query parameters:
      | property           | value                                         |
      | subject:identifier | https://fhir.nhs.uk/Id/nhs-number\|9278693472 |
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
    Given Consumer "Yorkshire Ambulance Service" (Organisation ID "RX898") is requesting to search Document Pointers
    And Consumer "Yorkshire Ambulance Service" is registered in the system for application "DataShare" (ID "z00z-y11y-x22x") with pointer types
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
      | custodian   | 8HX13                            |
      | subject     | 9278693472                       |
      | contentType | application/pdf                  |
      | url         | https://example.org/my-doc-2.pdf |
    And a Document Pointer exists in the system with the below values for DOCUMENT template
      | property    | value                            |
      | identifier  | 3334567890                       |
      | type        | 555553002                        |
      | custodian   | C0D9R                            |
      | subject     | 9278693472                       |
      | contentType | application/pdf                  |
      | url         | https://example.org/my-doc-2.pdf |
    When Consumer "Yorkshire Ambulance Service" searches for Document References with query parameters:
      | property           | value                                         |
      | subject:identifier | https://fhir.nhs.uk/Id/nhs-number\|9278693472 |
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
      | custodian   | 8HX13                            |
      | subject     | 9278693472                       |
      | contentType | application/pdf                  |
      | url         | https://example.org/my-doc-2.pdf |

  Scenario: Empty results when searching for a Document Pointer when the consumer can't access existing document type
    Given Consumer "Yorkshire Ambulance Service" (Organisation ID "RX898") is requesting to search Document Pointers
    And Consumer "Yorkshire Ambulance Service" is registered in the system for application "DataShare" (ID "z00z-y11y-x22x") with pointer types
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    And a Document Pointer exists in the system with the below values for DOCUMENT template
      | property    | value                          |
      | identifier  | 1114567890                     |
      | type        | 999253002                      |
      | custodian   | 8FW23                          |
      | subject     | 9278693472                     |
      | contentType | application/pdf                |
      | url         | https://example.org/my-doc.pdf |
    When Consumer "Yorkshire Ambulance Service" searches for Document References with query parameters:
      | property           | value                                         |
      | subject:identifier | https://fhir.nhs.uk/Id/nhs-number\|9278693472 |
    Then the operation is successful

  Scenario: Empty results when searching for a Document Pointer when subject has no documents
    Given Consumer "Yorkshire Ambulance Service" (Organisation ID "RX898") is requesting to search Document Pointers
    And Consumer "Yorkshire Ambulance Service" is registered in the system for application "DataShare" (ID "z00z-y11y-x22x") with pointer types
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    When Consumer "Yorkshire Ambulance Service" searches for Document References with query parameters:
      | property           | value                                         |
      | subject:identifier | https://fhir.nhs.uk/Id/nhs-number\|9278693472 |
    Then the operation is successful

  Scenario: Successfully searches for all documents by producer and nhs number for a consumer
    Given Consumer "Yorkshire Ambulance Service" (Organisation ID "RX898") is requesting to search Document Pointers
    And Consumer "Yorkshire Ambulance Service" is registered in the system for application "DataShare" (ID "z00z-y11y-x22x") with pointer types
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
      | type        | 999253002                      |
      | custodian   | RY26A                          |
      | subject     | 9278693472                     |
      | contentType | application/pdf                |
      | url         | https://example.org/my-doc.pdf |
    When Consumer "Yorkshire Ambulance Service" searches for Document References with query parameters:
      | property             | value                                               |
      | subject:identifier   | https://fhir.nhs.uk/Id/nhs-number\|9278693472       |
      | custodian:identifier | https://fhir.nhs.uk/Id/ods-organization-code\|8FW23 |
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

  Scenario: Successfully searches for all documents by type and nhs number for a consumer
    Given Consumer "Yorkshire Ambulance Service" (Organisation ID "RX898") is requesting to search Document Pointers
    And Consumer "Yorkshire Ambulance Service" is registered in the system for application "DataShare" (ID "z00z-y11y-x22x") with pointer types
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
      | identifier  | 1114567891                     |
      | type        | 999253002                      |
      | custodian   | 8FW23                          |
      | subject     | 9278693472                     |
      | contentType | application/pdf                |
      | url         | https://example.org/my-doc.pdf |
    When Consumer "Yorkshire Ambulance Service" searches for Document References with query parameters:
      | property           | value                                         |
      | subject:identifier | https://fhir.nhs.uk/Id/nhs-number\|9278693472 |
      | type               | http://snomed.info/sct\|736253002             |
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

  Scenario: Successfully searches for all documents by producer and nhs number and type for a consumer
    Given Consumer "Yorkshire Ambulance Service" (Organisation ID "RX898") is requesting to search Document Pointers
    And Consumer "Yorkshire Ambulance Service" is registered in the system for application "DataShare" (ID "z00z-y11y-x22x") with pointer types
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
      | identifier  | 1114567891                     |
      | type        | 999253002                      |
      | custodian   | 8FW23                          |
      | subject     | 9278693472                     |
      | contentType | application/pdf                |
      | url         | https://example.org/my-doc.pdf |
    When Consumer "Yorkshire Ambulance Service" searches for Document References with query parameters:
      | property             | value                                               |
      | subject:identifier   | https://fhir.nhs.uk/Id/nhs-number\|9278693472       |
      | custodian:identifier | https://fhir.nhs.uk/Id/ods-organization-code\|8FW23 |
      | type                 | http://snomed.info/sct\|736253002                   |
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
    Given Consumer "Yorkshire Ambulance Service" (Organisation ID "RX898") is requesting to search Document Pointers
    And Consumer "Yorkshire Ambulance Service" is registered in the system for application "DataShare" (ID "z00z-y11y-x22x") with pointer types
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    And 21 Document Pointers exists in the system with the below values for DOCUMENT template
      | property    | value                          |
      | identifier  | 11145678______                 |
      | type        | 736253002                      |
      | custodian   | 8FW23                          |
      | subject     | 9278693472                     |
      | contentType | application/pdf                |
      | url         | https://example.org/my-doc.pdf |
    When Consumer "Yorkshire Ambulance Service" searches for Document References with query parameters:
      | property             | value                                               |
      | subject:identifier   | https://fhir.nhs.uk/Id/nhs-number\|9278693472       |
      | custodian:identifier | https://fhir.nhs.uk/Id/ods-organization-code\|8FW23 |
      | type                 | http://snomed.info/sct\|736253002                   |
    Then the operation is successful
    And the response is a Bundle with 20 entries
    And the Bundle contains an Entry with the below values for DOCUMENT template
      | property    | value                          |
      | identifier  | 11145678000000                 |
      | type        | 736253002                      |
      | custodian   | 8FW23                          |
      | subject     | 9278693472                     |
      | contentType | application/pdf                |
      | url         | https://example.org/my-doc.pdf |
    And the Bundle contains a next page token
    When Consumer "Yorkshire Ambulance Service" searches for the next page
    Then the operation is successful
    And the response is a Bundle with 1 entries
    And the Bundle contains an Entry with the below values for DOCUMENT template
      | property    | value                          |
      | identifier  | 11145678000020                 |
      | type        | 736253002                      |
      | custodian   | 8FW23                          |
      | subject     | 9278693472                     |
      | contentType | application/pdf                |
      | url         | https://example.org/my-doc.pdf |

  Scenario: Successfully searches for all documents by producer and nhs number and type for a consumer - using permissions stored in s3 auth
    Given Consumer "Yorkshire Ambulance Service" (Organisation ID "RX898") is requesting to search Document Pointers
    And Consumer "Yorkshire Ambulance Service" is registered in the system for application "DataShare" (ID "z00z-y11y-x22x") with pointer types stored in NRLF
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
      | identifier  | 1114567891                     |
      | type        | 999253002                      |
      | custodian   | 8FW23                          |
      | subject     | 9278693472                     |
      | contentType | application/pdf                |
      | url         | https://example.org/my-doc.pdf |
    When Consumer "Yorkshire Ambulance Service" searches for Document References with query parameters:
      | property             | value                                               |
      | subject:identifier   | https://fhir.nhs.uk/Id/nhs-number\|9278693472       |
      | custodian:identifier | https://fhir.nhs.uk/Id/ods-organization-code\|8FW23 |
      | type                 | http://snomed.info/sct\|736253002                   |
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
