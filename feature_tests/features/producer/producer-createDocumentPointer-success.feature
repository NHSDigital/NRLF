Feature: Producer Create Success scenarios

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
                  "system": "https://fhir.nhs.uk/CodeSystem/NRLF-SuccessCode"
                }
              ]
            }
          }
        ]
      }
      """

  Scenario: Successfully create a Document Pointer of type Mental health crisis plan
    Given Producer "Aaron Court Mental Health NH" (Organisation ID "8FW23") is requesting to create Document Pointers
    And Producer "Aaron Court Mental Health NH" is registered in the system for application "DataShare" (ID "z00z-y11y-x22x") with pointer types
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    When Producer "Aaron Court Mental Health NH" creates a Document Reference from DOCUMENT template
      | property    | value                          |
      | identifier  | 1234567890                     |
      | type        | 736253002                      |
      | custodian   | 8FW23                          |
      | subject     | 9278693472                     |
      | contentType | application/pdf                |
      | url         | https://example.org/my-doc.pdf |
    Then the operation is successful
    And the status is 201
    And Document Pointer "8FW23-1234567890" exists
      | property    | value                             |
      | id          | 8FW23-1234567890                  |
      | nhs_number  | 9278693472                        |
      | producer_id | 8FW23                             |
      | type        | http://snomed.info/sct\|736253002 |
      | source      | NRLF                              |
      | version     | 1                                 |
      | updated_on  | NULL                              |
      | document    | <document>                        |
      | created_on  | <timestamp>                       |

  Scenario: Successfully create a Document Pointer of type End of life care coordination summary
    Given Producer "Aaron Court Mental Health NH" (Organisation ID "8FW23") is requesting to create Document Pointers
    And Producer "Aaron Court Mental Health NH" is registered in the system for application "DataShare" (ID "z00z-y11y-x22x") with pointer types
      | system                 | value           |
      | http://snomed.info/sct | 861421000000109 |
    When Producer "Aaron Court Mental Health NH" creates a Document Reference from DOCUMENT template
      | property    | value                          |
      | identifier  | 1234567891                     |
      | type        | 861421000000109                |
      | custodian   | 8FW23                          |
      | subject     | 2742179658                     |
      | contentType | application/pdf                |
      | url         | https://example.org/my-doc.pdf |
    Then the operation is successful
    And the status is 201
    And the response is an OperationOutcome according to the OUTCOME template with the below values
      | property          | value            |
      | issue_type        | informational    |
      | issue_level       | information      |
      | issue_code        | RESOURCE_CREATED |
      | issue_description | Resource created |
      | message           | Resource created |
    And Document Pointer "8FW23-1234567891" exists
      | property    | value                                   |
      | id          | 8FW23-1234567891                        |
      | nhs_number  | 2742179658                              |
      | producer_id | 8FW23                                   |
      | type        | http://snomed.info/sct\|861421000000109 |
      | source      | NRLF                                    |
      | version     | 1                                       |
      | updated_on  | NULL                                    |
      | document    | <document>                              |
      | created_on  | <timestamp>                             |
