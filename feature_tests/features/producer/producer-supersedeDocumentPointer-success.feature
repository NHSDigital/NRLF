Feature: Producer Supersede Success scenarios

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
                  "system": "https://fhir.nhs.uk/CodeSystem/NRLF-SuccessCode"
                }
              ]
            }
          }
        ]
      }
      """

  Scenario: Supersede multiple Document Pointers
    Given Producer "Aaron Court Mental Health NH" (Organisation ID "8FW23") is requesting to create Document Pointers
    And Producer "Aaron Court Mental Health NH" is registered in the system for application "DataShare" (ID "z00z-y11y-x22x") with pointer types
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    And a Document Pointer exists in the system with the below values for DOCUMENT template
      | property    | value                          |
      | identifier  | 8FW23-1234567890               |
      | type        | 736253002                      |
      | custodian   | 8FW23                          |
      | subject     | 9278693472                     |
      | contentType | application/pdf                |
      | url         | https://example.org/my-doc.pdf |
    And a Document Pointer exists in the system with the below values for DOCUMENT template
      | property    | value                          |
      | identifier  | 8FW23-1234567891               |
      | type        | 736253002                      |
      | custodian   | 8FW23                          |
      | subject     | 9278693472                     |
      | contentType | application/pdf                |
      | url         | https://example.org/my-doc.pdf |
    When Producer "Aaron Court Mental Health NH" creates a Document Reference from DOCUMENT template
      | property    | value                          |
      | identifier  | 8FW23-1234567892               |
      | target      | 8FW23-1234567890               |
      | target      | 8FW23-1234567891               |
      | type        | 736253002                      |
      | custodian   | 8FW23                          |
      | subject     | 9278693472                     |
      | contentType | application/pdf                |
      | url         | https://example.org/my-doc.pdf |
    Then the operation is successful
    And the response is an OperationOutcome according to the OUTCOME template with the below values
      | property          | value                                    |
      | issue_type        | informational                            |
      | issue_level       | information                              |
      | issue_code        | RESOURCE_SUPERSEDED                      |
      | issue_description | Resource created and Resource(s) deleted |
      | message           | Resource created and Resource(s) deleted |
    And Document Pointer "8FW23-1234567892" exists
      | property    | value                             |
      | id          | 8FW23-1234567892                  |
      | nhs_number  | 9278693472                        |
      | producer_id | 8FW23                             |
      | type        | http://snomed.info/sct\|736253002 |
      | source      | NRLF                              |
      | version     | 1                                 |
      | updated_on  | NULL                              |
      | document    | <document>                        |
      | created_on  | <timestamp>                       |
    And Document Pointer "8FW23-1234567890" does not exist
    And Document Pointer "8FW23-1234567891" does not exist
