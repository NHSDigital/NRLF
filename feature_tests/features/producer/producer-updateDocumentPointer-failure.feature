Feature: Producer Update Failure scenarios

  Background:
    Given template DOCUMENT:
      """
      {
        "resourceType": "DocumentReference",
        "id": "$custodian-$identifier",
        "custodian": {
          "identifier": {
            "system": "$cust_id_sys",
            "value": "$custodian"
          }
        },
        "subject": {
          "identifier": {
            "system": "$subj_id_sys",
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
        "status": "$status",
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
    And template BAD_DOCUMENT
      """
      {
      "bad":$bad
      }
      """
    And template DOCUMENT_WITH_INVALID_ID_FORMAT
      """
      {
        "resourceType": "DocumentReference",
        "id": "$custodian|$identifier",
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

  Scenario: Unable to update a Document Pointer that does not exist
    Given Producer "Aaron Court Mental Health NH" (Organisation ID "8FW23") is requesting to update Document Pointers
    And Producer "Aaron Court Mental Health NH" is registered in the system for application "DataShare" (ID "z00z-y11y-x22x") with pointer types
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    And a Document Pointer exists in the system with the below values for DOCUMENT template
      | property    | value                                       |
      | identifier  | 1234567890                                  |
      | type        | 736253002                                   |
      | custodian   | 8FW23                                       |
      | subject     | 9278693472                                  |
      | contentType | application/pdf                             |
      | status      | current                                     |
      | url         | https://example.org/my-doc.pdf              |
      | cust_id_sys | https://fhir.nhs.uk/Id/accredited-system-id |
      | subj_id_sys | https://fhir.nhs.uk/Id/nhs-number           |
    When Producer "Aaron Court Mental Health NH" updates Document Reference "8FW23-0987654321" from DOCUMENT template
      | property    | value                                 |
      | identifier  | 1234567890                            |
      | status      | current                               |
      | type        | 736253002                             |
      | custodian   | 8FW23                                 |
      | subject     | 9278693472                            |
      | contentType | application/pdf                       |
      | url         | https://example.org/different-doc.pdf |
    Then the operation is unsuccessful
    And the response is an OperationOutcome according to the OUTCOME template with the below values
      | property          | value                   |
      | issue_type        | processing              |
      | issue_level       | error                   |
      | issue_code        | RESOURCE_NOT_FOUND      |
      | issue_description | Resource not found      |
      | message           | Item could not be found |

  Scenario: Unable to update the relatesTo immutable property of a DOCUMENT_POINTER
    Given Producer "Aaron Court Mental Health NH" (Organisation ID "8FW23") is requesting to update Document Pointers
    And Producer "Aaron Court Mental Health NH" is registered in the system for application "DataShare" (ID "z00z-y11y-x22x") with pointer types
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    And a Document Pointer exists in the system with the below values for DOCUMENT template
      | property    | value                                       |
      | identifier  | 1234567890                                  |
      | type        | 736253002                                   |
      | custodian   | 8FW23                                       |
      | subject     | 9278693472                                  |
      | contentType | application/pdf                             |
      | status      | current                                     |
      | url         | https://example.org/my-doc.pdf              |
      | cust_id_sys | https://fhir.nhs.uk/Id/accredited-system-id |
      | subj_id_sys | https://fhir.nhs.uk/Id/nhs-number           |
    When Producer "Aaron Court Mental Health NH" updates Document Reference "8FW23-1234567890" from DOCUMENT template
      | property    | value                                       |
      | identifier  | 1234567890                                  |
      | status      | current                                     |
      | type        | 736253002                                   |
      | custodian   | 8FW23                                       |
      | subject     | 9278693472                                  |
      | contentType | application/pdf                             |
      | target      | 536941082                                   |
      | cust_id_sys | https://fhir.nhs.uk/Id/accredited-system-id |
      | subj_id_sys | https://fhir.nhs.uk/Id/nhs-number           |
    Then the operation is unsuccessful
    And the response is an OperationOutcome according to the OUTCOME template with the below values
      | property          | value                                                   |
      | issue_type        | processing                                              |
      | issue_level       | error                                                   |
      | issue_code        | VALIDATION_ERROR                                        |
      | issue_description | A parameter or value has resulted in a validation error |
      | message           | Trying to update one or more immutable fields           |

  Scenario: Unable to update the status immutable property of a DOCUMENT_POINTER
    Given Producer "Aaron Court Mental Health NH" (Organisation ID "8FW23") is requesting to update Document Pointers
    And Producer "Aaron Court Mental Health NH" is registered in the system for application "DataShare" (ID "z00z-y11y-x22x") with pointer types
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    And a Document Pointer exists in the system with the below values for DOCUMENT template
      | property    | value                                       |
      | identifier  | 1234567890                                  |
      | type        | 736253002                                   |
      | custodian   | 8FW23                                       |
      | subject     | 9278693472                                  |
      | contentType | application/pdf                             |
      | status      | current                                     |
      | url         | https://example.org/my-doc.pdf              |
      | cust_id_sys | https://fhir.nhs.uk/Id/accredited-system-id |
      | subj_id_sys | https://fhir.nhs.uk/Id/nhs-number           |
    When Producer "Aaron Court Mental Health NH" updates Document Reference "8FW23-1234567890" from DOCUMENT template
      | property    | value                                       |
      | identifier  | 1234567890                                  |
      | status      | deleted                                     |
      | type        | 736253002                                   |
      | custodian   | 8FW23                                       |
      | subject     | 9278693472                                  |
      | contentType | application/pdf                             |
      | cust_id_sys | https://fhir.nhs.uk/Id/accredited-system-id |
      | subj_id_sys | https://fhir.nhs.uk/Id/nhs-number           |
    Then the operation is unsuccessful
    And the response is an OperationOutcome according to the OUTCOME template with the below values
      | property          | value                                                   |
      | issue_type        | processing                                              |
      | issue_level       | error                                                   |
      | issue_code        | VALIDATION_ERROR                                        |
      | issue_description | A parameter or value has resulted in a validation error |
      | message           | Trying to update one or more immutable fields           |

  Scenario: Unable to update Document Pointer
    Given Producer "Aaron Court Mental Health NH" (Organisation ID "8FW23") is requesting to update Document Pointers
    And Producer "Aaron Court Mental Health NH" is registered in the system for application "DataShare" (ID "z00z-y11y-x22x") with pointer types
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    And a Document Pointer exists in the system with the below values for DOCUMENT template
      | property    | value                                       |
      | identifier  | 1234567890                                  |
      | type        | 736253002                                   |
      | custodian   | 8FW23                                       |
      | subject     | 9278693472                                  |
      | contentType | application/pdf                             |
      | status      | current                                     |
      | url         | https://example.org/my-doc.pdf              |
      | cust_id_sys | https://fhir.nhs.uk/Id/accredited-system-id |
      | subj_id_sys | https://fhir.nhs.uk/Id/nhs-number           |
    When Producer "Aaron Court Mental Health NH" updates Document Reference "8FW23-1234567890" from BAD_DOCUMENT template
      | property | value |
      | bad      | true  |
    Then the operation is unsuccessful
    And the status is 400
    And the response is an OperationOutcome according to the OUTCOME template with the below values
      | property          | value                                                       |
      | issue_type        | processing                                                  |
      | issue_level       | error                                                       |
      | issue_code        | VALIDATION_ERROR                                            |
      | issue_description | A parameter or value has resulted in a validation error     |
      | message           | DocumentReference validation failure - Invalid resourceType |

  Scenario: Unable to update Document Pointer with an invalid id format
    Given Producer "Aaron Court Mental Health NH" (Organisation ID "8FW23") is requesting to update Document Pointers
    And Producer "Aaron Court Mental Health NH" is registered in the system for application "DataShare" (ID "z00z-y11y-x22x") with pointer types
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    And a Document Pointer exists in the system with the below values for DOCUMENT template
      | property    | value                                       |
      | identifier  | 1234567890                                  |
      | type        | 736253002                                   |
      | custodian   | 8FW23                                       |
      | subject     | 9278693472                                  |
      | contentType | application/pdf                             |
      | status      | current                                     |
      | url         | https://example.org/my-doc.pdf              |
      | cust_id_sys | https://fhir.nhs.uk/Id/accredited-system-id |
      | subj_id_sys | https://fhir.nhs.uk/Id/nhs-number           |
    When Producer "Aaron Court Mental Health NH" updates Document Reference "8FW23-1234567890" from DOCUMENT_WITH_INVALID_ID_FORMAT template
      | property    | value           |
      | identifier  | 1234567890      |
      | status      | deleted         |
      | type        | 736253002       |
      | custodian   | 8FW23           |
      | subject     | 9278693472      |
      | contentType | application/pdf |
    Then the operation is unsuccessful
    And the status is 404
    And the response is an OperationOutcome according to the OUTCOME template with the below values
      | property          | value                   |
      | issue_type        | processing              |
      | issue_level       | error                   |
      | issue_code        | RESOURCE_NOT_FOUND      |
      | issue_description | Resource not found      |
      | message           | Item could not be found |

  Scenario: Unable to update a Document Pointer with an invalid tuple id format
    Given Producer "Aaron Court Mental Health NH" (Organisation ID "8FW23") is requesting to update Document Pointers
    And Producer "Aaron Court Mental Health NH" is registered in the system for application "DataShare" (ID "z00z-y11y-x22x") with pointer types
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    And a Document Pointer exists in the system with the below values for DOCUMENT template
      | property    | value                                       |
      | identifier  | 1234567890                                  |
      | type        | 736253002                                   |
      | custodian   | 8FW23                                       |
      | subject     | 9278693472                                  |
      | contentType | application/pdf                             |
      | status      | current                                     |
      | url         | https://example.org/my-doc.pdf              |
      | cust_id_sys | https://fhir.nhs.uk/Id/accredited-system-id |
      | subj_id_sys | https://fhir.nhs.uk/Id/nhs-number           |
    When Producer "Aaron Court Mental Health NH" updates Document Reference "8FW23|1234567890" from DOCUMENT template
      | property    | value                                       |
      | identifier  | 1234567890                                  |
      | status      | deleted                                     |
      | type        | 736253002                                   |
      | custodian   | 8FW23                                       |
      | subject     | 9278693472                                  |
      | contentType | application/pdf                             |
      | cust_id_sys | https://fhir.nhs.uk/Id/accredited-system-id |
      | subj_id_sys | https://fhir.nhs.uk/Id/nhs-number           |
    Then the operation is unsuccessful
    And the status is 400
    And the response is an OperationOutcome according to the OUTCOME template with the below values
      | property          | value                                                     |
      | issue_type        | processing                                                |
      | issue_level       | error                                                     |
      | issue_code        | VALIDATION_ERROR                                          |
      | issue_description | A parameter or value has resulted in a validation error   |
      | message           | Input is not composite of the form a-b: 8FW23\|1234567890 |

  Scenario: Unable to update a Document Pointer when the status value is empty in Document Reference
    Given Producer "Aaron Court Mental Health NH" (Organisation ID "8FW23") is requesting to update Document Pointers
    And Producer "Aaron Court Mental Health NH" is registered in the system for application "DataShare" (ID "z00z-y11y-x22x") with pointer types
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    And a Document Pointer exists in the system with the below values for DOCUMENT template
      | property    | value                                       |
      | identifier  | 1234567890                                  |
      | type        | 736253002                                   |
      | custodian   | 8FW23                                       |
      | subject     | 9278693472                                  |
      | contentType | application/pdf                             |
      | status      | current                                     |
      | url         | https://example.org/my-doc.pdf              |
      | cust_id_sys | https://fhir.nhs.uk/Id/accredited-system-id |
      | subj_id_sys | https://fhir.nhs.uk/Id/nhs-number           |
    When Producer "Aaron Court Mental Health NH" updates Document Reference "8FW23-1234567890" from DOCUMENT template
      | property    | value                                       |
      | identifier  | 1234567890                                  |
      | status      |                                             |
      | type        | 736253002                                   |
      | custodian   | 8FW23                                       |
      | subject     | 9278693472                                  |
      | contentType | application/pdf                             |
      | url         | https://example.org/different-doc.pdf       |
      | cust_id_sys | https://fhir.nhs.uk/Id/accredited-system-id |
      | subj_id_sys | https://fhir.nhs.uk/Id/nhs-number           |
    Then the operation is unsuccessful
    And the status is 400
    And the response is an OperationOutcome according to the OUTCOME template with the below values
      | property          | value                                                   |
      | issue_type        | processing                                              |
      | issue_level       | error                                                   |
      | issue_code        | VALIDATION_ERROR                                        |
      | issue_description | A parameter or value has resulted in a validation error |
      | message           | DocumentReference validation failure - Invalid status   |

  Scenario: Unable to update a Document Pointer when the custodian identifier system is empty in Document Reference
    Given Producer "Aaron Court Mental Health NH" (Organisation ID "8FW23") is requesting to update Document Pointers
    And Producer "Aaron Court Mental Health NH" is registered in the system for application "DataShare" (ID "z00z-y11y-x22x") with pointer types
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    And a Document Pointer exists in the system with the below values for DOCUMENT template
      | property    | value                                       |
      | identifier  | 1234567890                                  |
      | type        | 736253002                                   |
      | custodian   | 8FW23                                       |
      | subject     | 9278693472                                  |
      | contentType | application/pdf                             |
      | status      | current                                     |
      | url         | https://example.org/my-doc.pdf              |
      | cust_id_sys | https://fhir.nhs.uk/Id/accredited-system-id |
      | subj_id_sys | https://fhir.nhs.uk/Id/nhs-number           |
    When Producer "Aaron Court Mental Health NH" updates Document Reference "8FW23-1234567890" from DOCUMENT template
      | property    | value                                 |
      | identifier  | 1234567890                            |
      | status      | current                               |
      | type        | 736253002                             |
      | custodian   | 8FW23                                 |
      | subject     | 9278693472                            |
      | contentType | application/pdf                       |
      | url         | https://example.org/different-doc.pdf |
      | cust_id_sys |                                       |
      | subj_id_sys | https://fhir.nhs.uk/Id/nhs-number     |
    Then the operation is unsuccessful
    And the status is 400
    And the response is an OperationOutcome according to the OUTCOME template with the below values
      | property          | value                                                    |
      | issue_type        | processing                                               |
      | issue_level       | error                                                    |
      | issue_code        | VALIDATION_ERROR                                         |
      | issue_description | A parameter or value has resulted in a validation error  |
      | message           | DocumentReference validation failure - Invalid custodian |

  Scenario: Unable to update a Document Pointer when the custodian identifier value is empty in Document Reference
    Given Producer "Aaron Court Mental Health NH" (Organisation ID "8FW23") is requesting to update Document Pointers
    And Producer "Aaron Court Mental Health NH" is registered in the system for application "DataShare" (ID "z00z-y11y-x22x") with pointer types
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    And a Document Pointer exists in the system with the below values for DOCUMENT template
      | property    | value                                       |
      | identifier  | 1234567890                                  |
      | type        | 736253002                                   |
      | custodian   | 8FW23                                       |
      | subject     | 9278693472                                  |
      | contentType | application/pdf                             |
      | status      | current                                     |
      | url         | https://example.org/my-doc.pdf              |
      | cust_id_sys | https://fhir.nhs.uk/Id/accredited-system-id |
      | subj_id_sys | https://fhir.nhs.uk/Id/nhs-number           |
    When Producer "Aaron Court Mental Health NH" updates Document Reference "8FW23-1234567890" from DOCUMENT template
      | property    | value                                       |
      | identifier  | 1234567890                                  |
      | status      | current                                     |
      | type        | 736253002                                   |
      | custodian   |                                             |
      | subject     | 9278693472                                  |
      | contentType | application/pdf                             |
      | url         | https://example.org/different-doc.pdf       |
      | cust_id_sys | https://fhir.nhs.uk/Id/accredited-system-id |
      | subj_id_sys | https://fhir.nhs.uk/Id/nhs-number           |
    Then the operation is unsuccessful
    And the status is 404
    And the response is an OperationOutcome according to the OUTCOME template with the below values
      | property          | value                   |
      | issue_type        | processing              |
      | issue_level       | error                   |
      | issue_code        | RESOURCE_NOT_FOUND      |
      | issue_description | Resource not found      |
      | message           | Item could not be found |

  Scenario: Unable to update a Document Pointer when the subject identifier system is empty in Document Reference
    Given Producer "Aaron Court Mental Health NH" (Organisation ID "8FW23") is requesting to update Document Pointers
    And Producer "Aaron Court Mental Health NH" is registered in the system for application "DataShare" (ID "z00z-y11y-x22x") with pointer types
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    And a Document Pointer exists in the system with the below values for DOCUMENT template
      | property    | value                                       |
      | identifier  | 1234567890                                  |
      | type        | 736253002                                   |
      | custodian   | 8FW23                                       |
      | subject     | 9278693472                                  |
      | contentType | application/pdf                             |
      | status      | current                                     |
      | url         | https://example.org/my-doc.pdf              |
      | cust_id_sys | https://fhir.nhs.uk/Id/accredited-system-id |
      | subj_id_sys | https://fhir.nhs.uk/Id/nhs-number           |
    When Producer "Aaron Court Mental Health NH" updates Document Reference "8FW23-1234567890" from DOCUMENT template
      | property    | value                                       |
      | identifier  | 1234567890                                  |
      | status      | current                                     |
      | type        | 736253002                                   |
      | custodian   | 8FW23                                       |
      | subject     | 9278693472                                  |
      | contentType | application/pdf                             |
      | url         | https://example.org/different-doc.pdf       |
      | cust_id_sys | https://fhir.nhs.uk/Id/accredited-system-id |
      | subj_id_sys |                                             |
    Then the operation is unsuccessful
    And the status is 400
    And the response is an OperationOutcome according to the OUTCOME template with the below values
      | property          | value                                                   |
      | issue_type        | processing                                              |
      | issue_level       | error                                                   |
      | issue_code        | VALIDATION_ERROR                                        |
      | issue_description | A parameter or value has resulted in a validation error |
      | message           | DocumentReference validation failure - Invalid subject  |

  Scenario: Unable to update a Document Pointer when the subject identifier value is empty in Document Reference
    Given Producer "Aaron Court Mental Health NH" (Organisation ID "8FW23") is requesting to update Document Pointers
    And Producer "Aaron Court Mental Health NH" is registered in the system for application "DataShare" (ID "z00z-y11y-x22x") with pointer types
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    And a Document Pointer exists in the system with the below values for DOCUMENT template
      | property    | value                                       |
      | identifier  | 1234567890                                  |
      | type        | 736253002                                   |
      | custodian   | 8FW23                                       |
      | subject     | 9278693472                                  |
      | contentType | application/pdf                             |
      | status      | current                                     |
      | url         | https://example.org/my-doc.pdf              |
      | cust_id_sys | https://fhir.nhs.uk/Id/accredited-system-id |
      | subj_id_sys | https://fhir.nhs.uk/Id/nhs-number           |
    When Producer "Aaron Court Mental Health NH" updates Document Reference "8FW23-1234567890" from DOCUMENT template
      | property    | value                                       |
      | identifier  | 1234567890                                  |
      | status      | current                                     |
      | type        | 736253002                                   |
      | custodian   | 8FW23                                       |
      | subject     |                                             |
      | contentType | application/pdf                             |
      | url         | https://example.org/different-doc.pdf       |
      | cust_id_sys | https://fhir.nhs.uk/Id/accredited-system-id |
      | subj_id_sys | https://fhir.nhs.uk/Id/nhs-number           |
    Then the operation is unsuccessful
    And the status is 400
    And the response is an OperationOutcome according to the OUTCOME template with the below values
      | property          | value                                                   |
      | issue_type        | processing                                              |
      | issue_level       | error                                                   |
      | issue_code        | VALIDATION_ERROR                                        |
      | issue_description | A parameter or value has resulted in a validation error |
      | message           | DocumentReference validation failure - Invalid subject  |

  Scenario: Unable to update a Document Pointer when the attachment url is empty in Document Reference
    Given Producer "Aaron Court Mental Health NH" (Organisation ID "8FW23") is requesting to update Document Pointers
    And Producer "Aaron Court Mental Health NH" is registered in the system for application "DataShare" (ID "z00z-y11y-x22x") with pointer types
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    And a Document Pointer exists in the system with the below values for DOCUMENT template
      | property    | value                                       |
      | identifier  | 1234567890                                  |
      | type        | 736253002                                   |
      | custodian   | 8FW23                                       |
      | subject     | 9278693472                                  |
      | contentType | application/pdf                             |
      | status      | current                                     |
      | url         | https://example.org/my-doc.pdf              |
      | cust_id_sys | https://fhir.nhs.uk/Id/accredited-system-id |
      | subj_id_sys | https://fhir.nhs.uk/Id/nhs-number           |
    When Producer "Aaron Court Mental Health NH" updates Document Reference "8FW23-1234567890" from DOCUMENT template
      | property    | value                                       |
      | identifier  | 1234567890                                  |
      | status      | current                                     |
      | type        | 736253002                                   |
      | custodian   | 8FW23                                       |
      | subject     | 9278693472                                  |
      | contentType | application/pdf                             |
      | url         |                                             |
      | cust_id_sys | https://fhir.nhs.uk/Id/accredited-system-id |
      | subj_id_sys | https://fhir.nhs.uk/Id/nhs-number           |
    Then the operation is unsuccessful
    And the status is 400
    And the response is an OperationOutcome according to the OUTCOME template with the below values
      | property          | value                                                   |
      | issue_type        | processing                                              |
      | issue_level       | error                                                   |
      | issue_code        | VALIDATION_ERROR                                        |
      | issue_description | A parameter or value has resulted in a validation error |
      | message           | DocumentReference validation failure - Invalid content  |

  Scenario: Unable to update a Document Pointer when the attachment contentType is empty in Document Reference
    Given Producer "Aaron Court Mental Health NH" (Organisation ID "8FW23") is requesting to update Document Pointers
    And Producer "Aaron Court Mental Health NH" is registered in the system for application "DataShare" (ID "z00z-y11y-x22x") with pointer types
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    And a Document Pointer exists in the system with the below values for DOCUMENT template
      | property    | value                                       |
      | identifier  | 1234567890                                  |
      | type        | 736253002                                   |
      | custodian   | 8FW23                                       |
      | subject     | 9278693472                                  |
      | contentType | application/pdf                             |
      | status      | current                                     |
      | url         | https://example.org/my-doc.pdf              |
      | cust_id_sys | https://fhir.nhs.uk/Id/accredited-system-id |
      | subj_id_sys | https://fhir.nhs.uk/Id/nhs-number           |
    When Producer "Aaron Court Mental Health NH" updates Document Reference "8FW23-1234567890" from DOCUMENT template
      | property    | value                                       |
      | identifier  | 1234567890                                  |
      | status      | current                                     |
      | type        | 736253002                                   |
      | custodian   | 8FW23                                       |
      | subject     | 9278693472                                  |
      | contentType |                                             |
      | url         | https://example.org/my-doc.pdf              |
      | cust_id_sys | https://fhir.nhs.uk/Id/accredited-system-id |
      | subj_id_sys | https://fhir.nhs.uk/Id/nhs-number           |
    Then the operation is unsuccessful
    And the status is 400
    And the response is an OperationOutcome according to the OUTCOME template with the below values
      | property          | value                                                   |
      | issue_type        | processing                                              |
      | issue_level       | error                                                   |
      | issue_code        | VALIDATION_ERROR                                        |
      | issue_description | A parameter or value has resulted in a validation error |
      | message           | DocumentReference validation failure - Invalid content  |
