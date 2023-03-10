Feature: Producer Delete Failure scenarios

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

  Scenario: Unable to delete a Document Pointer when the Producer does not have permission
    Given Producer "Aaron Court Mental Health NH" (Organisation ID "8FW23") is requesting to delete Document Pointers
    And Producer "Aaron Court Mental Health NH" is registered in the system for application "DataShare" (ID "z00z-y11y-x22x") with pointer types
      | system                 | value     |
      | http://snomed.info/sct | 736253001 |
    And a Document Pointer exists in the system with the below values for DOCUMENT template
      | property    | value                          |
      | identifier  | 1234567890                     |
      | type        | 736253001                      |
      | custodian   | 8FW23                          |
      | subject     | 9278693472                     |
      | contentType | application/pdf                |
      | url         | https://example.org/my-doc.pdf |
    When Producer "Aaron Court Mental Health NH" deletes an existing Document Reference "VLP01-1234567890"
    Then the operation is unsuccessful
    And the response is an OperationOutcome according to the OUTCOME template with the below values
      | property          | value                                                            |
      | issue_type        | processing                                                       |
      | issue_level       | error                                                            |
      | issue_code        | ACCESS_DENIED_LEVEL                                              |
      | issue_description | Access has been denied because you need higher level permissions |
      | message           | Required permissions to delete a document pointer are missing    |

  Scenario: Unable to delete a non-existing Document Pointer
    Given Producer "Aaron Court Mental Health NH" (Organisation ID "8FW23") is requesting to delete Document Pointers
    And Producer "Aaron Court Mental Health NH" is registered in the system for application "DataShare" (ID "z00z-y11y-x22x") with pointer types
      | system                 | value     |
      | http://snomed.info/sct | 736253001 |
    When Producer "Aaron Court Mental Health NH" deletes an existing Document Reference "8FW23-1234567890"
    Then the operation is unsuccessful
    And the response is an OperationOutcome according to the OUTCOME template with the below values
      | property          | value                   |
      | issue_type        | processing              |
      | issue_level       | error                   |
      | issue_code        | RESOURCE_NOT_FOUND      |
      | issue_description | Resource not found      |
      | message           | Item could not be found |

  Scenario: Unable to delete another organisations Document Pointer
    Given Producer "Aaron Court Mental Health NH" (Organisation ID "8FW23") is requesting to delete Document Pointers
    And Producer "Aaron Court Mental Health NH" is registered in the system for application "DataShare" (ID "z00z-y11y-x22x") with pointer types
      | system                 | value     |
      | http://snomed.info/sct | 736253001 |
    When Producer "Aaron Court Mental Health NH" deletes an existing Document Reference "VN6DL-1234567890"
    Then the operation is unsuccessful
    And the response is an OperationOutcome according to the OUTCOME template with the below values
      | property          | value                                                            |
      | issue_type        | processing                                                       |
      | issue_level       | error                                                            |
      | issue_code        | ACCESS_DENIED_LEVEL                                              |
      | issue_description | Access has been denied because you need higher level permissions |
      | message           | Required permissions to delete a document pointer are missing    |

  Scenario: Producer deletes a Document Pointer with an invalid tuple id format
    Given Producer "Aaron Court Mental Health NH" (Organisation ID "8FW23") is requesting to delete Document Pointers
    And Producer "Aaron Court Mental Health NH" is registered in the system for application "DataShare" (ID "z00z-y11y-x22x") with pointer types
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    And a Document Pointer exists in the system with the below values for DOCUMENT template
      | property    | value                          |
      | identifier  | 1234567890                     |
      | type        | 736253002                      |
      | custodian   | 8FW23                          |
      | subject     | 9278693472                     |
      | contentType | application/pdf                |
      | url         | https://example.org/my-doc.pdf |
    When Producer "Aaron Court Mental Health NH" deletes an existing Document Reference "8FW23|1234567890"
    Then the operation is unsuccessful
    And the status is 400
    And the response is an OperationOutcome according to the OUTCOME template with the below values
      | property          | value                                                     |
      | issue_type        | processing                                                |
      | issue_level       | error                                                     |
      | issue_code        | VALIDATION_ERROR                                          |
      | issue_description | A parameter or value has resulted in a validation error   |
      | message           | Input is not composite of the form a-b: 8FW23\|1234567890 |
