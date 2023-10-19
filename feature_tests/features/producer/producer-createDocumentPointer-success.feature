Feature: Producer Create Success scenarios

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
    And template DOCUMENT_WITH_DATE
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
        "date": "$date"
      }
      """
    And template DOCUMENT_WITH_AUTHOR
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
        "author": [
          {
            "identifier": {
              "system": "https://fhir.nhs.uk/Id/nhsSpineASID",
              "value": "200000000610"
            }
          },
          {
            "reference": "https://directory.spineservices.nhs.uk/STU3/Organization/RAT"
          }
        ],
        "status": "current"
      }
      """
    Given template DOCUMENT_WITH_CONTACT
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
          },
          {
            "attachment": {
              "contentType": "text/html",
              "url": "$contactUrl"
            }
          }
        ],
        "status": "current"
      }
      """
    Given template DOCUMENT_WITH_CONTACT_ONLY
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
              "contentType": "text/html",
              "url": "$contactUrl"
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
    And template JSON_SCHEMA
      """
      {
        "additionalProperties": true,
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "Validate Content Url",
        "type": "object",
        "properties": {
          "content": {
            "type": "array",
            "items": {
              "type": "object",
              "properties": {
                "attachment": {
                  "type": "object",
                  "properties": {
                    "url": {
                      "type": "string",
                      "pattern": "^https*://(www.)*\\w+.*$"
                    }
                  }
                }
              }
            }
          }
        }
      }
      """
    And template JSON_SCHEMA_DATE
      """
      {
        "$schema": "http://json-schema.org/draft-04/schema#",
        "title": "Validate Mandatory Date",
        "type": "object",
        "required": [
          "date"
        ],
        "properties": {
          "date": {
            "type": "string",
            "pattern": "^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}[+-]\\d{2}:\\d{2}$"
          }
        }
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

  Scenario: Successfully create a Document Pointer with content and contact details
    Given Producer "Aaron Court Mental Health NH" (Organisation ID "8FW23") is requesting to create Document Pointers
    And Producer "Aaron Court Mental Health NH" is registered in the system for application "DataShare" (ID "z00z-y11y-x22x") with pointer types
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    When Producer "Aaron Court Mental Health NH" creates a Document Reference from DOCUMENT_WITH_CONTACT template
      | property    | value                               |
      | identifier  | 1234567890                          |
      | type        | 736253002                           |
      | custodian   | 8FW23                               |
      | subject     | 9278693472                          |
      | contentType | application/pdf                     |
      | url         | https://example.org/my-doc.pdf      |
      | contactUrl  | https://example.org/my-contact.html |
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

  Scenario: Successfully create a Document Pointer with contact details only
    Given Producer "Aaron Court Mental Health NH" (Organisation ID "8FW23") is requesting to create Document Pointers
    And Producer "Aaron Court Mental Health NH" is registered in the system for application "DataShare" (ID "z00z-y11y-x22x") with pointer types
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    When Producer "Aaron Court Mental Health NH" creates a Document Reference from DOCUMENT_WITH_CONTACT_ONLY template
      | property   | value                               |
      | identifier | 1234567890                          |
      | type       | 736253002                           |
      | custodian  | 8FW23                               |
      | subject    | 9278693472                          |
      | contactUrl | https://example.org/my-contact.html |
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

  Scenario: Successfully create a Document Pointer when the producer has an extension code
    Given Producer "BaRS (EMIS)" (Organisation ID "V4T0L.YGMMC") is requesting to create Document Pointers
    And Producer "BaRS (EMIS)" is registered in the system for application "DataShare" (ID "z00z-y11y-x22x") with pointer types
      | system                 | value           |
      | http://snomed.info/sct | 861421000000109 |
    When Producer "BaRS (EMIS)" creates a Document Reference from DOCUMENT template
      | property    | value                          |
      | identifier  | 1234567891                     |
      | type        | 861421000000109                |
      | custodian   | V4T0L.YGMMC                    |
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
    And Document Pointer "V4T0L.YGMMC-1234567891" exists
      | property    | value                                   |
      | id          | V4T0L.YGMMC-1234567891                  |
      | nhs_number  | 2742179658                              |
      | producer_id | V4T0L.YGMMC                             |
      | type        | http://snomed.info/sct\|861421000000109 |
      | source      | NRLF                                    |
      | version     | 1                                       |
      | updated_on  | NULL                                    |
      | document    | <document>                              |
      | created_on  | <timestamp>                             |

  Scenario: Successfully create a Document Pointer with overridden created on date when producer has permission to set audit date
    Given Producer "Data Sync" (Organisation ID "DS123") is requesting to create Document Pointers
    And Producer "Data Sync" is registered in the system for application "DataShare" (ID "z00z-y11y-x22x") with pointer types stored in NRLF
      | system                 | value           |
      | http://snomed.info/sct | 861421000000109 |
    And Producer "Data Sync" has the permission "audit-dates-from-payload"
    When Producer "Data Sync" creates a Document Reference from DOCUMENT_WITH_DATE template
      | property    | value                          |
      | identifier  | 1234567891                     |
      | type        | 861421000000109                |
      | custodian   | DS123                          |
      | subject     | 2742179658                     |
      | contentType | application/pdf                |
      | url         | https://example.org/my-doc.pdf |
      | date        | 2023-05-02T12:00:00.000Z       |
    Then the operation is successful
    And the status is 201
    And the response is an OperationOutcome according to the OUTCOME template with the below values
      | property          | value            |
      | issue_type        | informational    |
      | issue_level       | information      |
      | issue_code        | RESOURCE_CREATED |
      | issue_description | Resource created |
      | message           | Resource created |
    And Document Pointer "DS123-1234567891" exists
      | property    | value                                   |
      | id          | DS123-1234567891                        |
      | nhs_number  | 2742179658                              |
      | producer_id | DS123                                   |
      | type        | http://snomed.info/sct\|861421000000109 |
      | source      | NRLF                                    |
      | version     | 1                                       |
      | updated_on  | NULL                                    |
      | document    | <document>                              |
      | created_on  | 2023-05-02T12:00:00.000Z                |

  @integration-only
  Scenario: Validate a Document Pointer of type TEST_TYPE with good URL
    Given Producer "Aaron Court Mental Health NH" (Organisation ID "8FW23") is requesting to create Document Pointers
    And Producer "Aaron Court Mental Health NH" is registered in the system for application "DataShare" (ID "z00z-y11y-x22x") with pointer types
      | system                 | value     |
      | http://snomed.info/sct | TEST_TYPE |
    # Remove the following line when NRLF-661 is implemented
    And the Data Contracts are loaded from the database
    And a Data Contract is registered in the system
      | property             | value                  |
      | name                 | Validate Content Url   |
      | system               | http://snomed.info/sct |
      | value                | TEST_TYPE              |
      | version              | 2000.01.01             |
      | inverse_version      | 0                      |
      | json_schema_template | JSON_SCHEMA            |
    And a Data Contract is registered in the system
      | property             | value                   |
      | name                 | Validate Mandatory Date |
      | system               | http://snomed.info/sct  |
      | value                | TEST_TYPE               |
      | version              | 2000.01.01              |
      | inverse_version      | 0                       |
      | json_schema_template | JSON_SCHEMA_DATE        |
    When Producer "Aaron Court Mental Health NH" creates a Document Reference from DOCUMENT_WITH_DATE template
      | property    | value                          |
      | identifier  | 1234567890                     |
      | type        | TEST_TYPE                      |
      | custodian   | 8FW23                          |
      | subject     | 9278693472                     |
      | contentType | application/pdf                |
      | url         | https://example.org/my-doc.pdf |
      | date        | 2022-12-21T10:45:41+11:00      |
    Then the operation is successful
    And the status is 201
    And Document Pointer "8FW23-1234567890" exists
      | property    | value                                                                                             |
      | id          | 8FW23-1234567890                                                                                  |
      | nhs_number  | 9278693472                                                                                        |
      | producer_id | 8FW23                                                                                             |
      | type        | http://snomed.info/sct\|TEST_TYPE                                                                 |
      | source      | NRLF                                                                                              |
      | version     | 1                                                                                                 |
      | schemas     | ["test-name:2000.01.01", "Validate Content Url:2000.01.01", "Validate Mandatory Date:2000.01.01"] |
      | updated_on  | NULL                                                                                              |
      | document    | <document>                                                                                        |
      | created_on  | <timestamp>                                                                                       |

  @integration-only
  Scenario: Validate a Document Pointer of type Mental health crisis plan using the asid data contract with no ssp and asid
    Given Producer "Aaron Court Mental Health NH" (Organisation ID "8FW23") is requesting to create Document Pointers
    And Producer "Aaron Court Mental Health NH" is registered in the system for application "DataShare" (ID "z00z-y11y-x22x") with pointer types
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    And the Data Contracts are loaded from the database
    When Producer "Aaron Court Mental Health NH" creates a Document Reference from DOCUMENT_WITH_AUTHOR template
      | property    | value                                    |
      | identifier  | 1234567890                               |
      | type        | 736253002                                |
      | custodian   | 8FW23                                    |
      | subject     | 9278693472                               |
      | contentType | application/html                         |
      | url         | https://example.org/contact-details.html |
    Then the operation is successful
    And the status is 201
    And Document Pointer "8FW23-1234567890" exists
      | property    | value                                                     |
      | id          | 8FW23-1234567890                                          |
      | nhs_number  | 9278693472                                                |
      | producer_id | 8FW23                                                     |
      | type        | http://snomed.info/sct\|736253002                         |
      | source      | NRLF                                                      |
      | version     | 1                                                         |
      | schemas     | ["test-name:2000.01.01", "asidcheck-contract:2000.01.01"] |
      | updated_on  | NULL                                                      |
      | document    | <document>                                                |
      | created_on  | <timestamp>                                               |

  @integration-only
  Scenario Outline: Validate a Care Plan Document Pointer type using the asid data contract with ssp and asid
    Given Producer "Aaron Court Mental Health NH" (Organisation ID "8FW23") is requesting to create Document Pointers
    And Producer "Aaron Court Mental Health NH" is registered in the system for application "DataShare" (ID "z00z-y11y-x22x") with pointer types
      | system                 | value  |
      | http://snomed.info/sct | <type> |
    And the Data Contracts are loaded from the database
    When Producer "Aaron Court Mental Health NH" creates a Document Reference from DOCUMENT_WITH_AUTHOR template
      | property    | value                        |
      | identifier  | 1234567890                   |
      | type        | <type>                       |
      | custodian   | 8FW23                        |
      | subject     | 9278693472                   |
      | contentType | application/pdf              |
      | url         | ssp://example.org/my-doc.pdf |
    Then the operation is successful
    And the status is 201
    And Document Pointer "8FW23-1234567890" exists
      | property    | value                                                     |
      | id          | 8FW23-1234567890                                          |
      | nhs_number  | 9278693472                                                |
      | producer_id | 8FW23                                                     |
      | type        | http://snomed.info/sct\|<type>                            |
      | source      | NRLF                                                      |
      | version     | 1                                                         |
      | schemas     | ["test-name:2000.01.01", "asidcheck-contract:2000.01.01"] |
      | updated_on  | NULL                                                      |
      | document    | <document>                                                |
      | created_on  | <timestamp>                                               |

    Examples:
      | type             |
      | 736253002        |
      | 325691000000100  |
      | 887701000000100  |
      | 861421000000109  |
      | 736373009        |
      | 1382601000000107 |
      | 1363501000000100 |
      | 24761000000103   |

  @integration-only
  Scenario: Validate a Document Pointer of type Mental health crisis plan using the asid data contract with no ssp and no asid
    Given Producer "Aaron Court Mental Health NH" (Organisation ID "8FW23") is requesting to create Document Pointers
    And Producer "Aaron Court Mental Health NH" is registered in the system for application "DataShare" (ID "z00z-y11y-x22x") with pointer types
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    And the Data Contracts are loaded from the database
    When Producer "Aaron Court Mental Health NH" creates a Document Reference from DOCUMENT template
      | property    | value                                    |
      | identifier  | 1234567890                               |
      | type        | 736253002                                |
      | custodian   | 8FW23                                    |
      | subject     | 9278693472                               |
      | contentType | application/html                         |
      | url         | https://example.org/contact-details.html |
    Then the operation is successful
    And the status is 201
    And Document Pointer "8FW23-1234567890" exists
      | property    | value                                                     |
      | id          | 8FW23-1234567890                                          |
      | nhs_number  | 9278693472                                                |
      | producer_id | 8FW23                                                     |
      | type        | http://snomed.info/sct\|736253002                         |
      | source      | NRLF                                                      |
      | version     | 1                                                         |
      | schemas     | ["test-name:2000.01.01", "asidcheck-contract:2000.01.01"] |
      | updated_on  | NULL                                                      |
      | document    | <document>                                                |
      | created_on  | <timestamp>                                               |
