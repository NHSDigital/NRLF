Feature: Producer Read Edge Case scenarios

  Background:
    Given template INVALID_AUTHOR_DOCUMENT
      """
      {
        "resourceType": "DocumentReference",
        "id": "$custodian-$identifier",
        "author": {
          "identifier": {
            "value": "Practitioner/A985657ZA"
          }
        },
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

  Scenario: Does not return document pointer that has invalid document reference data
    Given Producer "Aaron Court Mental Health NH" (Organisation ID "8FW23") is requesting to read Document Pointers
    And Producer "Aaron Court Mental Health NH" is registered in the system for application "DataShare" (ID "z00z-y11y-x22x") with pointer types
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    And an invalid Document Pointer exists in the system with the below values for INVALID_AUTHOR_DOCUMENT template
      | property    | value                          |
      | identifier  | 1234567890                     |
      | type        | 736253002                      |
      | custodian   | 8FW23                          |
      | subject     | 9278693472                     |
      | contentType | application/pdf                |
      | url         | https://example.org/my-doc.pdf |
    When Producer "Aaron Court Mental Health NH" reads an existing Document Reference "8FW23-1234567890"
    Then the operation is unsuccessful
    And the status is 500
    And the response is an OperationOutcome according to the OUTCOME template with the below values
      | property          | value                                               |
      | issue_type        | processing                                          |
      | issue_level       | error                                               |
      | issue_code        | SERVICE_ERROR                                       |
      | issue_description | Service failure or unexpected error                 |
      | message           | There was a problem retrieving the document pointer |
