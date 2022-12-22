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
                "value": "$target"
              }
            }
          }
        ]
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

  Scenario: Unable to update a Document Pointer that does not exist
    Given Producer "Aaron Court Mental Health NH" (Organisation ID "8FW23") is requesting to update Document Pointers
    And Producer "Aaron Court Mental Health NH" is registered in the system for application "DataShare" (ID "z00z-y11y-x22x") with pointer types
      | system                  | value     |
      | https://snomed.info/ict | 736253002 |
    And a Document Pointer exists in the system with the below values for DOCUMENT template
      | property    | value                          |
      | identifier  | 1234567890                     |
      | type        | 736253002                      |
      | custodian   | 8FW23                          |
      | subject     | 9278693472                     |
      | contentType | application/pdf                |
      | status      | current                        |
      | url         | https://example.org/my-doc.pdf |
    When Producer "Aaron Court Mental Health NH" updates Document Reference "8FW23|0987654321" from DOCUMENT template
      | property    | value                                 |
      | identifier  | 1234567890                            |
      | status      | current                               |
      | type        | 736253002                             |
      | custodian   | 8FW23                                 |
      | subject     | 9278693472                            |
      | contentType | application/pdf                       |
      | url         | https://example.org/different-doc.pdf |
    Then the operation is unsuccessful
    And the response is an OperationOutcome according to the OUTCOME template with the below values
      | property          | value                   |
      | issue_type        | processing              |
      | issue_level       | error                   |
      | issue_code        | RESOURCE_NOT_FOUND      |
      | issue_description | Resource not found      |
      | message           | Item could not be found |

  Scenario: Unable to update a Document Pointer when Producer does not have permission for existing types
    Given Producer "Aaron Court Mental Health NH" (Organisation ID "8FW23") is requesting to update Document Pointers
    And Producer "Aaron Court Mental Health NH" is registered in the system for application "DataShare" (ID "z00z-y11y-x22x") with pointer types
      | system                  | value     |
      | https://snomed.info/ict | 736253003 |
    And a Document Pointer exists in the system with the below values for DOCUMENT template
      | property    | value                          |
      | identifier  | 1234567890                     |
      | type        | 736253002                      |
      | custodian   | 8FW23                          |
      | subject     | 9278693472                     |
      | contentType | application/pdf                |
      | status      | current                        |
      | url         | https://example.org/my-doc.pdf |
    When Producer "Aaron Court Mental Health NH" updates Document Reference "8FW23|0987654321" from DOCUMENT template
      | property    | value                                 |
      | identifier  | 1234567890                            |
      | type        | 736253002                             |
      | custodian   | 8FW23                                 |
      | subject     | 9278693472                            |
      | contentType | application/pdf                       |
      | url         | https://example.org/different-doc.pdf |
    Then the operation is unsuccessful
    And the response is an OperationOutcome according to the OUTCOME template with the below values
      | property          | value                                                            |
      | issue_type        | processing                                                       |
      | issue_level       | error                                                            |
      | issue_code        | ACCESS_DENIED_LEVEL                                              |
      | issue_description | Access has been denied because you need higher level permissions |
      | message           | Required permissions to create a document pointer are missing    |

  Scenario: Unable to update the relatesTo immutable property of a DOCUMENT_POINTER
    Given Producer "Aaron Court Mental Health NH" (Organisation ID "8FW23") is requesting to update Document Pointers
    And Producer "Aaron Court Mental Health NH" is registered in the system for application "DataShare" (ID "z00z-y11y-x22x") with pointer types
      | system                  | value     |
      | https://snomed.info/ict | 736253002 |
    And a Document Pointer exists in the system with the below values for DOCUMENT template
      | property    | value                          |
      | identifier  | 1234567890                     |
      | type        | 736253002                      |
      | custodian   | 8FW23                          |
      | subject     | 9278693472                     |
      | contentType | application/pdf                |
      | status      | current                        |
      | url         | https://example.org/my-doc.pdf |
    When Producer "Aaron Court Mental Health NH" updates Document Reference "8FW23|1234567890" from DOCUMENT template
      | property    | value           |
      | identifier  | 1234567890      |
      | status      | current         |
      | type        | 736253002       |
      | custodian   | 8FW23           |
      | subject     | 9278693472      |
      | contentType | application/pdf |
      | target      | 536941082       |
    Then the operation is unsuccessful
    And the response is an OperationOutcome according to the OUTCOME template with the below values
      | property          | value                                                   |
      | issue_type        | processing                                              |
      | issue_level       | error                                                   |
      | issue_code        | VALIDATION_ERROR                                        |
      | issue_description | A parameter or value has resulted in a validation error |
      | message           | Trying to update one or more immutable fields           |

  Scenario: Unable to update the status immutable property of a DOCUMENT_POINTER
    Given Producer "Aaron Court Mental Health NH" (Organisation ID "8FW23") is requesting to update Document Pointers
    And Producer "Aaron Court Mental Health NH" is registered in the system for application "DataShare" (ID "z00z-y11y-x22x") with pointer types
      | system                  | value     |
      | https://snomed.info/ict | 736253002 |
    And a Document Pointer exists in the system with the below values for DOCUMENT template
      | property    | value                          |
      | identifier  | 1234567890                     |
      | type        | 736253002                      |
      | custodian   | 8FW23                          |
      | subject     | 9278693472                     |
      | contentType | application/pdf                |
      | status      | current                        |
      | url         | https://example.org/my-doc.pdf |
    When Producer "Aaron Court Mental Health NH" updates Document Reference "8FW23|1234567890" from DOCUMENT template
      | property    | value           |
      | identifier  | 1234567890      |
      | status      | deleted         |
      | type        | 736253002       |
      | custodian   | 8FW23           |
      | subject     | 9278693472      |
      | contentType | application/pdf |
    Then the operation is unsuccessful
    And the response is an OperationOutcome according to the OUTCOME template with the below values
      | property          | value                                                   |
      | issue_type        | processing                                              |
      | issue_level       | error                                                   |
      | issue_code        | VALIDATION_ERROR                                        |
      | issue_description | A parameter or value has resulted in a validation error |
      | message           | Trying to update one or more immutable fields           |
