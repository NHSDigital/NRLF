Feature: Producer Update Success scenarios

  Background:
    Given template DOCUMENT:
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

  Scenario Outline: Successfully update the mutable properties of a Document Pointer with only one change
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
      | property    | value           |
      | identifier  | 1234567890      |
      | status      | current         |
      | type        | 736253002       |
      | custodian   | 8FW23           |
      | subject     | 9278693472      |
      | contentType | application/pdf |
      | <property>  | <value>         |
    Then the operation is successful
    And the response is an OperationOutcome according to the OUTCOME template with the below values
      | property          | value            |
      | issue_type        | informational    |
      | issue_level       | information      |
      | issue_code        | RESOURCE_UPDATED |
      | issue_description | Resource updated |
      | message           | Resource updated |
    And Document Pointer "8FW23-1234567890" exists
      | property    | value                             |
      | id          | 8FW23-1234567890                  |
      | nhs_number  | 9278693472                        |
      | producer_id | 8FW23                             |
      | type        | http://snomed.info/sct\|736253002 |
      | source      | NRLF                              |
      | version     | 1                                 |
      | document    | <document>                        |
      | created_on  | <timestamp>                       |
      | updated_on  | <timestamp>                       |

    Examples:
      | property    | value                                           |
      | docStatus   | amended                                         |
      | author      | Organization/1XR                                |
      | description | Therapy Summary Document for Patient 9278693472 |
      | url         | https://example.org/different-doc.pdf           |

  Scenario: Successfully update the mutable properties of a Document Pointer with multiple changes
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
      | identifier  | 1234567890                                      |
      | status      | current                                         |
      | type        | 736253002                                       |
      | custodian   | 8FW23                                           |
      | subject     | 9278693472                                      |
      | contentType | application/pdf                                 |
      | docStatus   | amended                                         |
      | author      | Organization/1XR                                |
      | description | Therapy Summary Document for Patient 9278693472 |
      | url         | https://example.org/different-doc.pdf           |
    Then the operation is successful
    And the response is an OperationOutcome according to the OUTCOME template with the below values
      | property          | value            |
      | issue_type        | informational    |
      | issue_level       | information      |
      | issue_code        | RESOURCE_UPDATED |
      | issue_description | Resource updated |
      | message           | Resource updated |
    And Document Pointer "8FW23-1234567890" exists
      | property    | value                             |
      | id          | 8FW23-1234567890                  |
      | nhs_number  | 9278693472                        |
      | producer_id | 8FW23                             |
      | type        | http://snomed.info/sct\|736253002 |
      | source      | NRLF                              |
      | version     | 1                                 |
      | document    | <document>                        |
      | created_on  | <timestamp>                       |
      | updated_on  | <timestamp>                       |
