Feature: Consumer Search Failure scenarios

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

  Scenario: Search fails to return a bundle when extra parameters are found
    Given Consumer "Yorkshire Ambulance Service" (Organisation ID "RX898") is requesting to count Document Pointers
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
    When Consumer "Yorkshire Ambulance Service" counts Document References with query parameters:
      | property           | value                                         |
      | subject:identifier | https://fhir.nhs.uk/Id/nhs-number\|9278693472 |
      | extra              | unwanted field                                |
    Then the operation is unsuccessful
    And the status is 400
    And the response is an OperationOutcome according to the OUTCOME template with the below values
      | property          | value                                                   |
      | issue_type        | processing                                              |
      | issue_level       | error                                                   |
      | issue_code        | VALIDATION_ERROR                                        |
      | issue_description | A parameter or value has resulted in a validation error |
      | message           | Unexpected parameters: extra                            |

  Scenario: Subject is required
    Given Consumer "Yorkshire Ambulance Service" (Organisation ID "RX898") is requesting to count Document Pointers
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
    When Consumer "Yorkshire Ambulance Service" counts Document References with query parameters:
      | property | value |
    Then the operation is unsuccessful
    And the status is 400
    And the response is an OperationOutcome according to the OUTCOME template with the below values
      | property          | value                                                              |
      | issue_type        | processing                                                         |
      | issue_level       | error                                                              |
      | issue_code        | VALIDATION_ERROR                                                   |
      | issue_description | A parameter or value has resulted in a validation error            |
      | message           | CountRequestParams validation failure - Invalid subject:identifier |

  Scenario: Search fails when invalid subject:identifier used
    Given Consumer "Yorkshire Ambulance Service" (Organisation ID "RX898") is requesting to count Document Pointers
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
    When Consumer "Yorkshire Ambulance Service" counts Document References with query parameters:
      | property           | value            |
      | subject:identifier | Test\|9278693472 |
    Then the operation is unsuccessful
    And the status is 400
    And the response is an OperationOutcome according to the OUTCOME template with the below values
      | property          | value                                                              |
      | issue_type        | processing                                                         |
      | issue_level       | error                                                              |
      | issue_code        | VALIDATION_ERROR                                                   |
      | issue_description | A parameter or value has resulted in a validation error            |
      | message           | CountRequestParams validation failure - Invalid subject:identifier |
