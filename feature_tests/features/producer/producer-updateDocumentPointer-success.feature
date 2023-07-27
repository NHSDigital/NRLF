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
               "identifier" : {
                  "system" : "https://fhir.nhs.uk/Id/nhsSpineASID",
                  "value" : "200000000610"
               }
            },
            {
               "reference": "$author"
            }
         ],
         "description": "$description"
      }
      """
    Given template DOCUMENT_WITH_TITLE:
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
                  "url": "$url",
                  "title": "$contentTitle"
               }
            }
         ],
         "status": "current",
         "docStatus": "$docStatus",
         "author": [
            {
               "identifier" : {
                  "system" : "https://fhir.nhs.uk/Id/nhsSpineASID",
                  "value" : "200000000610"
               }
            },
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
    And template JSON_SCHEMA
      """
      {
         "$schema": "http://json-schema.org/draft-04/schema#",
         "type": "object",
         "title": "Validate Content Attachment Title",
         "properties": {
            "content": {
               "type": "array",
               "items": [
               {
                  "type": "object",
                  "properties": {
                     "attachment": {
                     "type": "object",
                     "properties": {
                        "title": {
                           "type": "string"
                        }
                     },
                     "required": [
                        "title"
                     ]
                     }
                  },
                  "required": [
                     "attachment"
                  ]
               }
               ]
            }
         },
         "required": [
            "content"
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
      | property    | value              |
      | identifier  | 1234567890         |
      | status      | current            |
      | type        | 736253002          |
      | custodian   | 8FW23              |
      | subject     | 9278693472         |
      | contentType | application/pdf    |
      | author      | Practitioner/xcda1 |
      | <property>  | <value>            |
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
      | author      | Practitioner/xcda1                              |
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

  Scenario: Successfully update the mutable properties of a Document Pointer with multiple changes for a producer with an extension code
    Given Producer "BaRS (South Derbyshire Mental Health Unit)" (Organisation ID "V4T0L.CBH") is requesting to update Document Pointers
    And Producer "BaRS (South Derbyshire Mental Health Unit)" is registered in the system for application "DataShare" (ID "z00z-y11y-x22x") with pointer types
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    And a Document Pointer exists in the system with the below values for DOCUMENT template
      | property    | value                          |
      | identifier  | 1234567890                     |
      | type        | 736253002                      |
      | custodian   | V4T0L.CBH                      |
      | subject     | 9278693472                     |
      | contentType | application/pdf                |
      | url         | https://example.org/my-doc.pdf |
      | docStatus   | preliminary                    |
      | author      | Practitioner/xcda1             |
      | description | Physical                       |
    When Producer "BaRS (South Derbyshire Mental Health Unit)" updates Document Reference "V4T0L.CBH-1234567890" from DOCUMENT template
      | property    | value                                           |
      | identifier  | 1234567890                                      |
      | status      | current                                         |
      | type        | 736253002                                       |
      | custodian   | V4T0L.CBH                                       |
      | subject     | 9278693472                                      |
      | contentType | application/pdf                                 |
      | docStatus   | amended                                         |
      | author      | Practitioner/xcda1                              |
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
    And Document Pointer "V4T0L.CBH-1234567890" exists
      | property    | value                             |
      | id          | V4T0L.CBH-1234567890              |
      | nhs_number  | 9278693472                        |
      | producer_id | V4T0L.CBH                         |
      | type        | http://snomed.info/sct\|736253002 |
      | source      | NRLF                              |
      | version     | 1                                 |
      | document    | <document>                        |
      | created_on  | <timestamp>                       |
      | updated_on  | <timestamp>                       |

  Scenario: Validate update operation against json schema
    Given Producer "Aaron Court Mental Health NH" (Organisation ID "8FW23") is requesting to update Document Pointers
    And Producer "Aaron Court Mental Health NH" is registered in the system for application "DataShare" (ID "z00z-y11y-x22x") with pointer types
      | system                 | value           |
      | http://snomed.info/sct | 887701000000100 |
    And a Data Contract is registered in the system
      | property             | value                             |
      | name                 | Validate Content Attachment Title |
      | system               | http://snomed.info/sct            |
      | value                | 887701000000100                   |
      | version              | 1                                 |
      | inverse_version      | 0                                 |
      | json_schema_template | JSON_SCHEMA                       |
    And a Document Pointer exists in the system with the below values for DOCUMENT_WITH_TITLE template
      | property    | value                          |
      | identifier  | 1234567890                     |
      | type        | 887701000000100                |
      | custodian   | 8FW23                          |
      | subject     | 9278693472                     |
      | contentType | application/pdf                |
      | url         | https://example.org/my-doc.pdf |
      | docStatus   | preliminary                    |
      | author      | Practitioner/xcda1             |
      | description | Physical                       |
      | title       | Title                          |
    When Producer "Aaron Court Mental Health NH" updates Document Reference "8FW23-1234567890" from DOCUMENT_WITH_TITLE template
      | property    | value                                           |
      | identifier  | 1234567890                                      |
      | status      | current                                         |
      | type        | 887701000000100                                 |
      | custodian   | 8FW23                                           |
      | subject     | 9278693472                                      |
      | contentType | application/pdf                                 |
      | docStatus   | amended                                         |
      | author      | Practitioner/xcda1                              |
      | description | Therapy Summary Document for Patient 9278693472 |
      | url         | https://example.org/different-doc.pdf           |
      | title       | Physical                                        |
    Then the operation is successful
    And the response is an OperationOutcome according to the OUTCOME template with the below values
      | property          | value            |
      | issue_type        | informational    |
      | issue_level       | information      |
      | issue_code        | RESOURCE_UPDATED |
      | issue_description | Resource updated |
      | message           | Resource updated |
    And Document Pointer "8FW23-1234567890" exists
      | property    | value                                   |
      | id          | 8FW23-1234567890                        |
      | nhs_number  | 9278693472                              |
      | producer_id | 8FW23                                   |
      | type        | http://snomed.info/sct\|887701000000100 |
      | source      | NRLF                                    |
      | version     | 1                                       |
      | schemas     | ["Validate Content Attachment Title:1"] |
      | document    | <document>                              |
      | created_on  | <timestamp>                             |
      | updated_on  | <timestamp>                             |
