Feature: Producer Update Failure scenarios

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
        ],
        "author" : [
          {
            "identifier" : {
              "system" : "$system",
              "value" : "$asid"
            }
          },
          {
            "reference" : "$author"
          }
        ]
      }
      """
    And template BAD_DOCUMENT
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
    And template DOCUMENT_WITH_INVALID_ID_FORMAT
      """
      {
        "resourceType": "DocumentReference",
        "id": "$custodian|$identifier",
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

  Scenario: Unable to update a Document Pointer that does not exist
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
      | status      | current                        |
      | url         | https://example.org/my-doc.pdf |
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
    And the status is 400
    And the response is an OperationOutcome according to the OUTCOME template with the below values
      | property          | value                                                           |
      | issue_type        | processing                                                      |
      | issue_level       | error                                                           |
      | issue_code        | VALIDATION_ERROR                                                |
      | issue_description | A parameter or value has resulted in a validation error         |
      | message           | Existing document id does not match the document id in the body |

  Scenario: Unable to update the relatesTo immutable property of a DOCUMENT_POINTER
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
      | status      | current                        |
      | url         | https://example.org/my-doc.pdf |
    When Producer "Aaron Court Mental Health NH" updates Document Reference "8FW23-1234567890" from DOCUMENT template
      | property    | value           |
      | identifier  | 1234567890      |
      | status      | current         |
      | type        | 736253002       |
      | custodian   | 8FW23           |
      | subject     | 9278693472      |
      | contentType | application/pdf |
      | target      | 536941082       |
    Then the operation is unsuccessful
    And the status is 400
    And the response is an OperationOutcome according to the OUTCOME template with the below values
      | property          | value                                                   |
      | issue_type        | processing                                              |
      | issue_level       | error                                                   |
      | issue_code        | VALIDATION_ERROR                                        |
      | issue_description | A parameter or value has resulted in a validation error |
      | message           | Forbidden to update immutable field 'relatesTo'         |

  Scenario: Unable to update the status immutable property of a DOCUMENT_POINTER
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
      | status      | current                        |
      | url         | https://example.org/my-doc.pdf |
    When Producer "Aaron Court Mental Health NH" updates Document Reference "8FW23-1234567890" from DOCUMENT template
      | property    | value           |
      | identifier  | 1234567890      |
      | status      | deleted         |
      | type        | 736253002       |
      | custodian   | 8FW23           |
      | subject     | 9278693472      |
      | contentType | application/pdf |
    Then the operation is unsuccessful
    And the status is 400
    And the response is an OperationOutcome according to the OUTCOME template with the below values
      | property          | value                                                   |
      | issue_type        | processing                                              |
      | issue_level       | error                                                   |
      | issue_code        | VALIDATION_ERROR                                        |
      | issue_description | A parameter or value has resulted in a validation error |
      | message           | Forbidden to update immutable field 'status'            |

  Scenario Outline: Unable to update the author immutable property of a DOCUMENT_POINTER
    Given Producer "Aaron Court Mental Health NH" (Organisation ID "8FW23") is requesting to update Document Pointers
    And Producer "Aaron Court Mental Health NH" is registered in the system for application "DataShare" (ID "z00z-y11y-x22x") with pointer types
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    And a Document Pointer exists in the system with the below values for DOCUMENT template
      | property    | value                                                        |
      | identifier  | 1234567890                                                   |
      | type        | 736253002                                                    |
      | custodian   | 8FW23                                                        |
      | subject     | 9278693472                                                   |
      | contentType | application/pdf                                              |
      | status      | current                                                      |
      | url         | https://example.org/my-doc.pdf                               |
      | asid        | 200000000610                                                 |
      | system      | https://fhir.nhs.uk/Id/nhsSpineASID                          |
      | author      | https://directory.spineservices.nhs.uk/STU3/Organization/RAE |
    When Producer "Aaron Court Mental Health NH" updates Document Reference "8FW23-1234567890" from DOCUMENT template
      | property    | value           |
      | identifier  | 1234567890      |
      | status      | current         |
      | type        | 736253002       |
      | custodian   | 8FW23           |
      | subject     | 9278693472      |
      | contentType | application/pdf |
      | <property>  | <value>         |
    Then the operation is unsuccessful
    And the status is 400
    And the response is an OperationOutcome according to the OUTCOME template with the below values
      | property          | value                                                   |
      | issue_type        | processing                                              |
      | issue_level       | error                                                   |
      | issue_code        | VALIDATION_ERROR                                        |
      | issue_description | A parameter or value has resulted in a validation error |
      | message           | Forbidden to update immutable field 'author'            |

    Examples:
      | property | value      |
      | asid     | new_asid   |
      | system   | new_system |
      | author   | new_author |

  Scenario: Unable to update Document Pointer when required type field is missing
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
      | status      | current                        |
      | url         | https://example.org/my-doc.pdf |
    When Producer "Aaron Court Mental Health NH" updates Document Reference "8FW23-1234567890" from BAD_DOCUMENT template
      | property    | value                          |
      | identifier  | 1234567890                     |
      | custodian   | 8FW23                          |
      | subject     | 9278693472                     |
      | contentType | application/pdf                |
      | status      | current                        |
      | url         | https://example.org/my-doc.pdf |
    Then the operation is unsuccessful
    And the status is 400
    And the response is an OperationOutcome according to the OUTCOME template with the below values
      | property          | value                                                   |
      | issue_type        | processing                                              |
      | issue_level       | error                                                   |
      | issue_code        | VALIDATION_ERROR                                        |
      | issue_description | A parameter or value has resulted in a validation error |
      | message           | The required field type is missing                      |

  Scenario: Unable to update Document Pointer with an invalid id format
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
      | status      | current                        |
      | url         | https://example.org/my-doc.pdf |
    When Producer "Aaron Court Mental Health NH" updates Document Reference "8FW23-1234567890" from DOCUMENT_WITH_INVALID_ID_FORMAT template
      | property    | value           |
      | identifier  | 1234567890      |
      | status      | deleted         |
      | type        | 736253002       |
      | custodian   | 8FW23           |
      | subject     | 9278693472      |
      | contentType | application/pdf |
    Then the operation is unsuccessful
    And the status is 400
    And the response is an OperationOutcome according to the OUTCOME template with the below values
      | property          | value                                                           |
      | issue_type        | processing                                                      |
      | issue_level       | error                                                           |
      | issue_code        | VALIDATION_ERROR                                                |
      | issue_description | A parameter or value has resulted in a validation error         |
      | message           | Existing document id does not match the document id in the body |

  Scenario: Unable to update a Document Pointer with an invalid tuple id format
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
      | status      | current                        |
      | url         | https://example.org/my-doc.pdf |
    When Producer "Aaron Court Mental Health NH" updates Document Reference "8FW23|1234567890" from DOCUMENT template
      | property    | value           |
      | identifier  | 1234567890      |
      | status      | deleted         |
      | type        | 736253002       |
      | custodian   | 8FW23           |
      | subject     | 9278693472      |
      | contentType | application/pdf |
    Then the operation is unsuccessful
    And the status is 400
    And the response is an OperationOutcome according to the OUTCOME template with the below values
      | property          | value                                                     |
      | issue_type        | processing                                                |
      | issue_level       | error                                                     |
      | issue_code        | VALIDATION_ERROR                                          |
      | issue_description | A parameter or value has resulted in a validation error   |
      | message           | Input is not composite of the form a-b: 8FW23\|1234567890 |

  Scenario: Unable to update a Document Pointer belonging to another organisation
    Given Producer "BaRS (South Derbyshire Mental Health Unit)" (Organisation ID "V4T0L.CBH") is requesting to update Document Pointers
    And Producer "BaRS (South Derbyshire Mental Health Unit)" is registered in the system for application "DataShare" (ID "z00z-y11y-x22x") with pointer types
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    And a Document Pointer exists in the system with the below values for DOCUMENT template
      | property    | value                          |
      | identifier  | 1234567890                     |
      | type        | 736253002                      |
      | custodian   | V4T0L                          |
      | subject     | 9278693472                     |
      | contentType | application/pdf                |
      | url         | https://example.org/my-doc.pdf |
      | docStatus   | preliminary                    |
      | author      | Practitioner/xcda1             |
      | description | Physical                       |
    When Producer "BaRS (South Derbyshire Mental Health Unit)" updates Document Reference "V4T0L-1234567890" from DOCUMENT template
      | property    | value                                           |
      | identifier  | 1234567890                                      |
      | status      | current                                         |
      | type        | 736253002                                       |
      | custodian   | V4T0L                                           |
      | subject     | 9278693472                                      |
      | contentType | application/pdf                                 |
      | docStatus   | amended                                         |
      | author      | Organization/1XR                                |
      | description | Therapy Summary Document for Patient 9278693472 |
      | url         | https://example.org/different-doc.pdf           |
    Then the operation is unsuccessful
    And the status is 400
    And the response is an OperationOutcome according to the OUTCOME template with the below values
      | property          | value                                                                        |
      | issue_type        | processing                                                                   |
      | issue_level       | error                                                                        |
      | issue_code        | VALIDATION_ERROR                                                             |
      | issue_description | A parameter or value has resulted in a validation error                      |
      | message           | The target document reference does not belong to the requesting organisation |
