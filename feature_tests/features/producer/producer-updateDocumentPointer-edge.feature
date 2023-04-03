Feature: Producer Update Success scenarios

  Background:
    Given template DOCUMENT:
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
        "status": "current",
        "docStatus": "$docStatus",
        "author": [
          {
            "reference": "$author"
          }
        ],
        "description": "$description"
      }
      """
    And template DOCUMENT_EMPTY_CODING
      """
      {
        "resourceType": "DocumentReference",
        "id": "8FW23-1234567890",
        "custodian": {
          "identifier": {
            "system": "https://fhir.nhs.uk/Id/ods-organization-code",
            "value": "8FW23"
          }
        },
        "subject": {
          "identifier": {
            "system": "https://fhir.nhs.uk/Id/nhs-number",
            "value": "9278693472"
          }
        },
        "type": {
          "coding": []
        },
        "content": [
          {
            "attachment": {
              "contentType": "application/pdf",
              "url": "https://example.org/my-doc.pdf"
            }
          }
        ],
        "status": "current"
      }
      """
    And template DOCUMENT_EMPTY_CONTENT
      """
      {
        "resourceType": "DocumentReference",
        "id": "8FW23-1234567890",
        "custodian": {
          "identifier": {
            "system": "https://fhir.nhs.uk/Id/ods-organization-code",
            "value": "8FW23"
          }
        },
        "subject": {
          "identifier": {
            "system": "https://fhir.nhs.uk/Id/nhs-number",
            "value": "9278693472"
          }
        },
        "type": {
          "coding": [
            {
              "system": "http://snomed.info/sct",
              "code": "736253002"
            }
          ]
        },
        "content": [
          {
            "attachment": {
              "contentType": "application/pdf",
              "url": ""
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

  Scenario: Unable to update Document Pointer when path id and body id are different
    Given Producer "Aaron Court Mental Health NH" (Organisation ID "8FW23") is requesting to update Document Pointers
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
      | docStatus   | preliminary                    |
      | author      | Practitioner/xcda1             |
      | description | Physical                       |
    When Producer "Aaron Court Mental Health NH" updates Document Reference "8FW23-1234567890" from DOCUMENT template
      | property    | value                                           |
      | identifier  | 1234567891                                      |
      | status      | current                                         |
      | type        | 736253002                                       |
      | custodian   | 8FW23                                           |
      | subject     | 9278693472                                      |
      | contentType | application/pdf                                 |
      | docStatus   | amended                                         |
      | author      | Organization/1XR                                |
      | description | Therapy Summary Document for Patient 9278693472 |
      | url         | https://example.org/different-doc.pdf           |
    Then the operation is unsuccessful
    And the status is 404
    And the response is an OperationOutcome according to the OUTCOME template with the below values
      | property          | value                   |
      | issue_type        | processing              |
      | issue_level       | error                   |
      | issue_code        | RESOURCE_NOT_FOUND      |
      | issue_description | Resource not found      |
      | message           | Item could not be found |

  Scenario: Requesting producer provides empty array
    Given Producer "Aaron Court Mental Health NH" (Organisation ID "8FW23") is requesting to update Document Pointers
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
    When Producer "Aaron Court Mental Health NH" updates Document Reference "8FW23-1234567890" from DOCUMENT_EMPTY_CODING template
      | property | value |
    Then the operation is unsuccessful
    And the response is an OperationOutcome according to the OUTCOME template with the below values
      | property          | value                                                   |
      | issue_type        | processing                                              |
      | issue_level       | error                                                   |
      | issue_code        | VALIDATION_ERROR                                        |
      | issue_description | A parameter or value has resulted in a validation error |
      | message           | Empty field 'coding' is not valid FHIR                  |

  Scenario: Requesting producer provides empty object
    Given Producer "Aaron Court Mental Health NH" (Organisation ID "8FW23") is requesting to update Document Pointers
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
    When Producer "Aaron Court Mental Health NH" updates Document Reference "8FW23-1234567890" from DOCUMENT_EMPTY_CONTENT template
      | property | value |
    Then the operation is unsuccessful
    And the response is an OperationOutcome according to the OUTCOME template with the below values
      | property          | value                                                   |
      | issue_type        | processing                                              |
      | issue_level       | error                                                   |
      | issue_code        | VALIDATION_ERROR                                        |
      | issue_description | A parameter or value has resulted in a validation error |
      | message           | Empty field 'url' is not valid FHIR                     |
