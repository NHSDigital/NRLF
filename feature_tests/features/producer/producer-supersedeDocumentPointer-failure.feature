Feature: Producer Supersede Failure scenarios

  Background:
    Given template DOCUMENT
      """
      {
        "resourceType": "DocumentReference",
        "id": "$identifier",
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
        "status": "current",
        "relatesTo": [
          {
            "code": "$code",
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
    And template BAD_DOCUMENT
      """
      {
        "resourceType": "DocumentReference",
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
    And template DOCUMENT_WITH_INVALID_ID_FORMAT
      """
      {
        "resourceType": "DocumentReference",
        "id": "$identifier",
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
    And template OUTCOME
      """
      {
        "resourceType": "OperationOutcome",
        "id": "<identifier>",
        "meta": {
          "profile": [
            "https://fhir.nhs.uk/StructureDefinition/NHSDigital-OperationOutcome"
          ]
        },
        "issue": [
          {
            "code": "$issue_type",
            "severity": "$issue_level",
            "diagnostics": "$message",
            "details": {
              "coding": [
                {
                  "code": "$issue_code",
                  "display": "$issue_description",
                  "system": "https://fhir.nhs.uk/CodeSystem/Spine-ErrorOrWarningCode"
                }
              ]
            }
          }
        ]
      }
      """

  Scenario: Producer does not have permission to create the supersede Document Pointer
    Given Producer "Aaron Court Mental Health NH" (Organisation ID "8FW23") is requesting to create Document Pointers
    And Producer "Aaron Court Mental Health NH" is registered in the system for application "DataShare" (ID "z00z-y11y-x22x") with pointer types
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    And a Document Pointer exists in the system with the below values for DOCUMENT template
      | property    | value                          |
      | identifier  | 8FW23-1234567890               |
      | type        | 736253002                      |
      | custodian   | 8FW23                          |
      | producer_id | 8FW23                          |
      | subject     | 9278693472                     |
      | contentType | application/pdf                |
      | url         | https://example.org/my-doc.pdf |
    When Producer "Aaron Court Mental Health NH" creates a Document Reference from DOCUMENT template
      | property    | value                          |
      | identifier  | 8FW23-1234567892               |
      | target      | 8FW23-1234567890               |
      | code        | replaces                       |
      | type        | 734163000                      |
      | custodian   | 8FW23                          |
      | producer_id | 8FW23                          |
      | subject     | 9278693472                     |
      | contentType | application/pdf                |
      | url         | https://example.org/my-doc.pdf |
    Then the operation is unsuccessful
    And the status is 400
    And the response is an OperationOutcome according to the OUTCOME template with the below values
      | property          | value                                                                                      |
      | issue_type        | processing                                                                                 |
      | issue_level       | error                                                                                      |
      | issue_code        | VALIDATION_ERROR                                                                           |
      | issue_description | A parameter or value has resulted in a validation error                                    |
      | message           | The type of the provided document pointer is not in the list of allowed types for this app |

  Scenario: Producer does not have permission to delete the superseded Document Pointer
    Given Producer "Aaron Court Mental Health NH" (Organisation ID "8FW23") is requesting to create Document Pointers
    And Producer "Aaron Court Mental Health NH" is registered in the system for application "DataShare" (ID "z00z-y11y-x22x") with pointer types
      | system                 | value     |
      | http://snomed.info/sct | 734163000 |
    And a Document Pointer exists in the system with the below values for DOCUMENT template
      | property    | value                          |
      | identifier  | 8FW23-1234567890               |
      | type        | 736253002                      |
      | custodian   | VN6DL                          |
      | producer_id | VN6DL                          |
      | subject     | 9278693472                     |
      | contentType | application/pdf                |
      | url         | https://example.org/my-doc.pdf |
    When Producer "Aaron Court Mental Health NH" creates a Document Reference from DOCUMENT template
      | property    | value                          |
      | identifier  | 8FW23-1234567892               |
      | target      | VN6DL-1234567890               |
      | code        | replaces                       |
      | type        | 734163000                      |
      | custodian   | 8FW23                          |
      | producer_id | 8FW23                          |
      | subject     | 9278693472                     |
      | contentType | application/pdf                |
      | url         | https://example.org/my-doc.pdf |
    Then the operation is unsuccessful
    And the status is 400
    And the response is an OperationOutcome according to the OUTCOME template with the below values
      | property          | value                                                                                      |
      | issue_type        | processing                                                                                 |
      | issue_level       | error                                                                                      |
      | issue_code        | VALIDATION_ERROR                                                                           |
      | issue_description | A parameter or value has resulted in a validation error                                    |
      | message           | At least one document pointer cannot be deleted because it belongs to another organisation |

  Scenario: The superseded Document Pointer does not exist
    Given Producer "Aaron Court Mental Health NH" (Organisation ID "8FW23") is requesting to create Document Pointers
    And Producer "Aaron Court Mental Health NH" is registered in the system for application "DataShare" (ID "z00z-y11y-x22x") with pointer types
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    When Producer "Aaron Court Mental Health NH" creates a Document Reference from DOCUMENT template
      | property    | value                          |
      | identifier  | 8FW23-1234567892               |
      | target      | 8FW23-1234567890               |
      | code        | replaces                       |
      | type        | 736253002                      |
      | custodian   | 8FW23                          |
      | producer_id | 8FW23                          |
      | subject     | 9278693472                     |
      | contentType | application/pdf                |
      | url         | https://example.org/my-doc.pdf |
    Then the operation is unsuccessful
    And the status is 400
    And the response is an OperationOutcome according to the OUTCOME template with the below values
      | property          | value                                                         |
      | issue_type        | processing                                                    |
      | issue_level       | error                                                         |
      | issue_code        | VALIDATION_ERROR                                              |
      | issue_description | A parameter or value has resulted in a validation error       |
      | message           | Validation failure - relatesTo target document does not exist |

  Scenario: Targets must be unique
    Given Producer "Aaron Court Mental Health NH" (Organisation ID "8FW23") is requesting to create Document Pointers
    And Producer "Aaron Court Mental Health NH" is registered in the system for application "DataShare" (ID "z00z-y11y-x22x") with pointer types
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    And a Document Pointer exists in the system with the below values for DOCUMENT template
      | property    | value                          |
      | identifier  | 8FW23-1234567890               |
      | type        | 736253002                      |
      | custodian   | 8FW23                          |
      | producer_id | 8FW23                          |
      | subject     | 9278693472                     |
      | contentType | application/pdf                |
      | url         | https://example.org/my-doc.pdf |
    When Producer "Aaron Court Mental Health NH" creates a Document Reference from DOCUMENT template
      | property    | value                          |
      | identifier  | 8FW23-1234567891               |
      | target      | 8FW23-1234567890               |
      | target      | 8FW23-1234567890               |
      | code        | replaces                       |
      | type        | 736253002                      |
      | custodian   | 8FW23                          |
      | producer_id | 8FW23                          |
      | subject     | 9278693472                     |
      | contentType | application/pdf                |
      | url         | https://example.org/my-doc.pdf |
    Then the operation is unsuccessful
    And the status is 400
    And the response is an OperationOutcome according to the OUTCOME template with the below values
      | property          | value                                          |
      | issue_type        | processing                                     |
      | issue_level       | error                                          |
      | issue_code        | INVALID_RESOURCE_ID                            |
      | issue_description | Invalid resource ID                            |
      | message           | Condition check failed - Supersede ID mismatch |

  Scenario: Unable to supersede a Document Pointer when required field id is missing
    Given Producer "Aaron Court Mental Health NH" (Organisation ID "8FW23") is requesting to create Document Pointers
    And Producer "Aaron Court Mental Health NH" is registered in the system for application "DataShare" (ID "z00z-y11y-x22x") with pointer types
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    And a Document Pointer exists in the system with the below values for DOCUMENT template
      | property    | value                          |
      | identifier  | 8FW23-1234567890               |
      | type        | 736253002                      |
      | custodian   | 8FW23                          |
      | producer_id | 8FW23                          |
      | subject     | 9278693472                     |
      | contentType | application/pdf                |
      | url         | https://example.org/my-doc.pdf |
    When Producer "Aaron Court Mental Health NH" creates a Document Reference from BAD_DOCUMENT template
      | property    | value                          |
      | identifier  | 8FW23-1234567890               |
      | type        | 736253002                      |
      | custodian   | 8FW23                          |
      | producer_id | 8FW23                          |
      | subject     | 9278693472                     |
      | contentType | application/pdf                |
      | url         | https://example.org/my-doc.pdf |
    Then the operation is unsuccessful
    And the status is 400
    And the response is an OperationOutcome according to the OUTCOME template with the below values
      | property          | value                                                   |
      | issue_type        | processing                                              |
      | issue_level       | error                                                   |
      | issue_code        | VALIDATION_ERROR                                        |
      | issue_description | A parameter or value has resulted in a validation error |
      | message           | The required field id is missing                        |

  Scenario: Unable to supersede a Document Pointer with an invalid id format
    Given Producer "Aaron Court Mental Health NH" (Organisation ID "8FW23") is requesting to create Document Pointers
    And Producer "Aaron Court Mental Health NH" is registered in the system for application "DataShare" (ID "z00z-y11y-x22x") with pointer types
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    When Producer "Aaron Court Mental Health NH" creates a Document Reference from DOCUMENT_WITH_INVALID_ID_FORMAT template
      | property    | value                          |
      | identifier  | 8FW23\|1234567890              |
      | type        | 736253002                      |
      | custodian   | 8FW23                          |
      | producer_id | 8FW23                          |
      | subject     | 9278693472                     |
      | contentType | application/pdf                |
      | url         | https://example.org/my-doc.pdf |
    Then the operation is unsuccessful
    And the status is 400
    And the response is an OperationOutcome according to the OUTCOME template with the below values
      | property          | value                                                     |
      | issue_type        | processing                                                |
      | issue_level       | error                                                     |
      | issue_code        | VALIDATION_ERROR                                          |
      | issue_description | A parameter or value has resulted in a validation error   |
      | message           | Input is not composite of the form a-b: 8FW23\|1234567890 |

  Scenario: Unable to supersede Document Pointer if the nhs number does not match
    Given Producer "Aaron Court Mental Health NH" (Organisation ID "8FW23") is requesting to create Document Pointers
    And Producer "Aaron Court Mental Health NH" is registered in the system for application "DataShare" (ID "z00z-y11y-x22x") with pointer types
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    And a Document Pointer exists in the system with the below values for DOCUMENT template
      | property    | value                          |
      | identifier  | 8FW23-1234567890               |
      | type        | 736253002                      |
      | custodian   | 8FW23                          |
      | producer_id | 8FW23                          |
      | subject     | 9278693472                     |
      | contentType | application/pdf                |
      | url         | https://example.org/my-doc.pdf |
    And a Document Pointer exists in the system with the below values for DOCUMENT template
      | property    | value                          |
      | identifier  | 8FW23-1234567891               |
      | type        | 736253002                      |
      | custodian   | 8FW23                          |
      | producer_id | 8FW23                          |
      | subject     | 9278693472                     |
      | contentType | application/pdf                |
      | url         | https://example.org/my-doc.pdf |
    When Producer "Aaron Court Mental Health NH" creates a Document Reference from DOCUMENT template
      | property    | value                          |
      | identifier  | 8FW23-1234567892               |
      | target      | 8FW23-1234567890               |
      | target      | 8FW23-1234567891               |
      | code        | replaces                       |
      | type        | 736253002                      |
      | custodian   | 8FW23                          |
      | producer_id | 8FW23                          |
      | subject     | 5387015366                     |
      | contentType | application/pdf                |
      | url         | https://example.org/my-doc.pdf |
    Then the operation is unsuccessful
    And the status is 400
    And the response is an OperationOutcome according to the OUTCOME template with the below values
      | property          | value                                                                                |
      | issue_type        | processing                                                                           |
      | issue_level       | error                                                                                |
      | issue_code        | VALIDATION_ERROR                                                                     |
      | issue_description | A parameter or value has resulted in a validation error                              |
      | message           | Validation failure - relatesTo target document nhs number does not match the request |
    And Document Pointer "8FW23-1234567892" does not exist
    And Document Pointer "8FW23-1234567890" still exists
    And Document Pointer "8FW23-1234567891" still exists

  Scenario: Unable to supersede Document Pointer if the type does not match
    Given Producer "Aaron Court Mental Health NH" (Organisation ID "8FW23") is requesting to create Document Pointers
    And Producer "Aaron Court Mental Health NH" is registered in the system for application "DataShare" (ID "z00z-y11y-x22x") with pointer types
      | system                 | value     |
      | http://snomed.info/sct | 736253001 |
      | http://snomed.info/sct | 736253002 |
    And a Document Pointer exists in the system with the below values for DOCUMENT template
      | property    | value                          |
      | identifier  | 8FW23-1234567890               |
      | type        | 736253002                      |
      | custodian   | 8FW23                          |
      | producer_id | 8FW23                          |
      | subject     | 9278693472                     |
      | contentType | application/pdf                |
      | url         | https://example.org/my-doc.pdf |
    And a Document Pointer exists in the system with the below values for DOCUMENT template
      | property    | value                          |
      | identifier  | 8FW23-1234567891               |
      | type        | 736253002                      |
      | custodian   | 8FW23                          |
      | producer_id | 8FW23                          |
      | subject     | 9278693472                     |
      | contentType | application/pdf                |
      | url         | https://example.org/my-doc.pdf |
    When Producer "Aaron Court Mental Health NH" creates a Document Reference from DOCUMENT template
      | property    | value                          |
      | identifier  | 8FW23-1234567892               |
      | target      | 8FW23-1234567890               |
      | target      | 8FW23-1234567891               |
      | code        | replaces                       |
      | type        | 736253001                      |
      | custodian   | 8FW23                          |
      | producer_id | 8FW23                          |
      | subject     | 9278693472                     |
      | contentType | application/pdf                |
      | url         | https://example.org/my-doc.pdf |
    Then the operation is unsuccessful
    And the status is 400
    And the response is an OperationOutcome according to the OUTCOME template with the below values
      | property          | value                                                                          |
      | issue_type        | processing                                                                     |
      | issue_level       | error                                                                          |
      | issue_code        | VALIDATION_ERROR                                                               |
      | issue_description | A parameter or value has resulted in a validation error                        |
      | message           | Validation failure - relatesTo target document type does not match the request |
    And Document Pointer "8FW23-1234567892" does not exist
    And Document Pointer "8FW23-1234567890" still exists
    And Document Pointer "8FW23-1234567891" still exists

  Scenario: relatesTo code is invalid
    Given Producer "Aaron Court Mental Health NH" (Organisation ID "8FW23") is requesting to create Document Pointers
    And Producer "Aaron Court Mental Health NH" is registered in the system for application "DataShare" (ID "z00z-y11y-x22x") with pointer types
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    And a Document Pointer exists in the system with the below values for DOCUMENT template
      | property    | value                          |
      | identifier  | 8FW23-1234567890               |
      | type        | 736253002                      |
      | custodian   | 8FW23                          |
      | producer_id | 8FW23                          |
      | subject     | 9278693472                     |
      | contentType | application/pdf                |
      | url         | https://example.org/my-doc.pdf |
    When Producer "Aaron Court Mental Health NH" creates a Document Reference from DOCUMENT template
      | property    | value                          |
      | identifier  | 8FW23-1234567892               |
      | target      | 8FW23-1234567890               |
      | code        | something_bad                  |
      | type        | 736253002                      |
      | custodian   | 8FW23                          |
      | producer_id | 8FW23                          |
      | subject     | 9278693472                     |
      | contentType | application/pdf                |
      | url         | https://example.org/my-doc.pdf |
    Then the operation is unsuccessful
    And the status is 400
    And the response is an OperationOutcome according to the OUTCOME template with the below values
      | property          | value                                                                                                                               |
      | issue_type        | processing                                                                                                                          |
      | issue_level       | error                                                                                                                               |
      | issue_code        | VALIDATION_ERROR                                                                                                                    |
      | issue_description | A parameter or value has resulted in a validation error                                                                             |
      | message           | Provided relatesTo code 'something_bad' must be one of ['appends', 'incorporates', 'replaces', 'signs', 'summarizes', 'transforms'] |

  Scenario: Unable to supersede another organisations Document Pointer due to id mismatch
    Given Producer "BaRS (EMIS)" (Organisation ID "V4T0L.YGMMC") is requesting to create Document Pointers
    And Producer "BaRS (EMIS)" is registered in the system for application "DataShare" (ID "z00z-y11y-x22x") with pointer types
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    And a Document Pointer exists in the system with the below values for DOCUMENT template
      | property    | value                          |
      | identifier  | V4T0L-1234567890               |
      | type        | 736253002                      |
      | custodian   | V4T0L                          |
      | producer_id | V4T0L                          |
      | subject     | 9278693472                     |
      | contentType | application/pdf                |
      | url         | https://example.org/my-doc.pdf |
    When Producer "BaRS (EMIS)" creates a Document Reference from DOCUMENT template
      | property    | value                          |
      | identifier  | V4T0L.YGMMC-1234567892         |
      | target      | V4T0L-1234567890               |
      | code        | replaces                       |
      | type        | 736253002                      |
      | custodian   | V4T0L                          |
      | producer_id | V4T0L                          |
      | subject     | 9278693472                     |
      | contentType | application/pdf                |
      | url         | https://example.org/my-doc.pdf |
    Then the operation is unsuccessful
    And the status is 400
    And the response is an OperationOutcome according to the OUTCOME template with the below values
      | property          | value                                                                                                     |
      | issue_type        | processing                                                                                                |
      | issue_level       | error                                                                                                     |
      | issue_code        | VALIDATION_ERROR                                                                                          |
      | issue_description | A parameter or value has resulted in a validation error                                                   |
      | message           | The custodian of the provided document pointer does not match the expected organisation code for this app |

  Scenario: Unable to supersede another organisations Document Pointer
    Given Producer "BaRS (EMIS)" (Organisation ID "V4T0L.YGMMC") is requesting to create Document Pointers
    And Producer "BaRS (EMIS)" is registered in the system for application "DataShare" (ID "z00z-y11y-x22x") with pointer types
      | system                 | value     |
      | http://snomed.info/sct | 734163000 |
    And a Document Pointer exists in the system with the below values for DOCUMENT template
      | property    | value                          |
      | identifier  | V4T0L-1234567890               |
      | type        | 734163000                      |
      | custodian   | V4T0L                          |
      | producer_id | V4T0L                          |
      | subject     | 9278693472                     |
      | contentType | application/pdf                |
      | url         | https://example.org/my-doc.pdf |
    When Producer "BaRS (EMIS)" creates a Document Reference from DOCUMENT template
      | property    | value                          |
      | identifier  | V4T0L.YGMMC-1234567892         |
      | target      | V4T0L-1234567890               |
      | code        | replaces                       |
      | type        | 734163000                      |
      | custodian   | V4T0L.YGMMC                    |
      | producer_id | V4T0L.YGMMC                    |
      | subject     | 9278693472                     |
      | contentType | application/pdf                |
      | url         | https://example.org/my-doc.pdf |
    Then the operation is unsuccessful
    And the status is 400
    And the response is an OperationOutcome according to the OUTCOME template with the below values
      | property          | value                                                                                      |
      | issue_type        | processing                                                                                 |
      | issue_level       | error                                                                                      |
      | issue_code        | VALIDATION_ERROR                                                                           |
      | issue_description | A parameter or value has resulted in a validation error                                    |
      | message           | At least one document pointer cannot be deleted because it belongs to another organisation |

  Scenario: Supersede throws a duplicate item when target doesnt exist and it tries to create a pointer that already exists
    Given Producer "Data Sync" (Organisation ID "DS123") is requesting to create Document Pointers
    And Producer "Data Sync" is registered in the system for application "DataShare" (ID "z00z-y11y-x22x") with pointer types stored in NRLF
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    And Producer "Data Sync" has the permission "supersede-ignore-delete-fail"
    And a Document Pointer exists in the system with the below values for DOCUMENT template
      | property    | value                          |
      | identifier  | DS123-1234567890               |
      | target      | DS123-1234567893               |
      | code        | replaces                       |
      | type        | 736253002                      |
      | custodian   | DS123                          |
      | producer_id | DS123                          |
      | subject     | 9278693472                     |
      | contentType | application/pdf                |
      | url         | https://example.org/my-doc.pdf |
    When Producer "Data Sync" creates a Document Reference from DOCUMENT template
      | property    | value                          |
      | identifier  | DS123-1234567890               |
      | target      | DS123-1234567893               |
      | code        | replaces                       |
      | type        | 736253002                      |
      | custodian   | DS123                          |
      | producer_id | DS123                          |
      | subject     | 9278693472                     |
      | contentType | application/pdf                |
      | url         | https://example.org/my-doc.pdf |
    Then the operation is unsuccessful
    And the status is 409
    And the response is an OperationOutcome according to the OUTCOME template with the below values
      | property          | value                                   |
      | issue_type        | processing                              |
      | issue_level       | error                                   |
      | issue_code        | INVALID_VALUE                           |
      | issue_description | Invalid value                           |
      | message           | Condition check failed - Duplicate item |
    And Document Pointer "DS123-1234567890" still exists
