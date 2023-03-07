Feature: Consumer Read Failure scenarios

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
            "severity": "$issue_level",
            "code": "$issue_type",
            "details": {
              "coding": [
                {
                  "system": "https://fhir.nhs.uk/CodeSystem/Spine-ErrorOrWarningCode",
                  "code": "$issue_code",
                  "display": "$issue_description"
                }
              ]
            },
            "diagnostics": "$message"
          }
        ]
      }
      """

  Scenario: Consumer permissions do not match the Document Pointer type
    Given Consumer "Yorkshire Ambulance Service" (Organisation ID "RX898") is requesting to read Document Pointers
    And Consumer "Yorkshire Ambulance Service" is registered in the system for application "DataShare" (ID "z00z-y11y-x22x") with pointer types
      | system                 | value     |
      | http://snomed.info/sct | 736253001 |
    And a Document Pointer exists in the system with the below values for DOCUMENT template
      | property    | value                          |
      | identifier  | 1234567890                     |
      | type        | 736253002                      |
      | custodian   | 8FW23                          |
      | subject     | 9278693472                     |
      | contentType | application/pdf                |
      | url         | https://example.org/my-doc.pdf |
    When Consumer "Yorkshire Ambulance Service" reads an existing Document Reference "8FW23-1234567890"
    Then the operation is unsuccessful
    And the response is an OperationOutcome according to the OUTCOME template with the below values
      | property          | value                   |
      | issue_type        | processing              |
      | issue_level       | error                   |
      | issue_code        | RESOURCE_NOT_FOUND      |
      | issue_description | Resource not found      |
      | message           | Item could not be found |

  Scenario: The Document Pointer does not exist
    Given Consumer "Yorkshire Ambulance Service" (Organisation ID "RX898") is requesting to read Document Pointers
    And Consumer "Yorkshire Ambulance Service" is registered in the system for application "DataShare" (ID "z00z-y11y-x22x") with pointer types
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    When Consumer "Yorkshire Ambulance Service" reads an existing Document Reference "8FW23-1234567890"
    Then the operation is unsuccessful
    And the response is an OperationOutcome according to the OUTCOME template with the below values
      | property          | value                   |
      | issue_type        | processing              |
      | issue_level       | error                   |
      | issue_code        | RESOURCE_NOT_FOUND      |
      | issue_description | Resource not found      |
      | message           | Item could not be found |

  Scenario: Consumer searches for a Document Pointer with an invalid tuple id format
    Given Consumer "Yorkshire Ambulance Service" (Organisation ID "RX898") is requesting to read Document Pointers
    And Consumer "Yorkshire Ambulance Service" is registered in the system for application "DataShare" (ID "z00z-y11y-x22x") with pointer types
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    When Consumer "Yorkshire Ambulance Service" reads an existing Document Reference "8FW23|1234567890"
    Then the operation is unsuccessful
    And the status is 400
    And the response is an OperationOutcome according to the OUTCOME template with the below values
      | property          | value                                                     |
      | issue_type        | processing                                                |
      | issue_level       | error                                                     |
      | issue_code        | VALIDATION_ERROR                                          |
      | issue_description | A parameter or value has resulted in a validation error   |
      | message           | Input is not composite of the form a-b: 8FW23\|1234567890 |
