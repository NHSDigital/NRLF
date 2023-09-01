Feature: Producer Create NRL-to-R4 Conversion

  Background:
    Given version "0.0.9" of "nrlf-converter" has been installed
    And template NRL_DOCUMENT_POINTER
      """
      {
          "attachment": {
              "url": "https://spine-proxy.national.ncrs.nhs.uk/p1.nhs.uk/MentalhealthCarePlanReportRGD.pdf",
              "creation": "2021-03-08T15:26:00+01:00",
              "contentType": "application/pdf"
          },
          "author": {
              "reference": "https://directory.spineservices.nhs.uk/STU3/Organization/RAE"
          },
          "class": {
              "coding": [
                  {
                      "system": "http://snomed.info/sct",
                      "code": "$classCode",
                      "display": "$classDisplay"
                  }
              ]
          },
          "content": [
              {
                  "attachment": {
                      "url": "$attachmentUrl",
                      "contentType": "$attachmentContentType",
                      "creation": "$attachmentCreation"
                  },
                  "format": {
                      "code": "urn:nhs-ic:unstructured",
                      "system": "https://fhir.nhs.uk/STU3/CodeSystem/NRL-FormatCode-1",
                      "display": "Unstructured Document"
                  }
              }
          ],
          "context": {
              "practiceSetting": {
                  "practiceSettingCoding": [
                      {
                          "code": "$practiceSettingCode",
                          "system": "http://snomed.info/sct",
                          "display": "$practiceSettingDisplay"
                      }
                  ]
              }
          },
          "custodian": {
              "reference": "$custodian"
          },
          "format": {
              "code": "urn:nhs-ic:unstructured",
              "system": "https://fhir.nhs.uk/STU3/CodeSystem/NRL-FormatCode-1",
              "display": "Unstructured Document"
          },
          "indexed": "$indexed",
          "lastModified": "$lastModified",
          "logicalIdentifier": {
              "logicalId": "$logicalId"
          },
          "meta": {
              "versionId": "1",
              "profile": [
                  "https://fhir.nhs.uk/STU3/StructureDefinition/NRL-DocumentReference-1"
              ],
              "lastUpdated": "Tue, 23 Aug 2022 14:45:17 GMT"
          },
          "relatesTo": {
              "code": "$relatesToCode",
              "target": {
                  "reference": "$relatesToTarget",
                  "identifier": {
                      "value": "$relatesToIdentifier",
                      "system": "$relatesToSystem"
                  }
              }
          },
          "removed": false,
          "stability": {
              "coding": [
                  {
                      "code": "dynamic",
                      "system": "https://fhir.nhs.uk/STU3/CodeSystem/NRL-ContentStability-1",
                      "display": "Dynamic"
                  }
              ]
          },
          "status": "current",
          "type": {
              "code": "$typeCode",
              "display": "$typeDisplay"
          }
      }
      """
    And template NRL_DOCUMENT_POINTER_WITHOUT_CONTEXT
      """
      {
          "attachment": {
              "url": "https://spine-proxy.national.ncrs.nhs.uk/p1.nhs.uk/MentalhealthCarePlanReportRGD.pdf",
              "creation": "2021-03-08T15:26:00+01:00",
              "contentType": "application/pdf"
          },
          "author": {
              "reference": "https://directory.spineservices.nhs.uk/STU3/Organization/RAE"
          },
          "class": {
              "coding": [
                  {
                      "system": "http://snomed.info/sct",
                      "code": "$classCode",
                      "display": "$classDisplay"
                  }
              ]
          },
          "content": [
              {
                  "attachment": {
                      "url": "$attachmentUrl",
                      "contentType": "$attachmentContentType",
                      "creation": "$attachmentCreation"
                  },
                  "format": {
                      "code": "urn:nhs-ic:unstructured",
                      "system": "https://fhir.nhs.uk/STU3/CodeSystem/NRL-FormatCode-1",
                      "display": "Unstructured Document"
                  }
              }
          ],
          "custodian": {
              "reference": "$custodian"
          },
          "format": {
              "code": "urn:nhs-ic:unstructured",
              "system": "https://fhir.nhs.uk/STU3/CodeSystem/NRL-FormatCode-1",
              "display": "Unstructured Document"
          },
          "indexed": "$indexed",
          "lastModified": "$lastModified",
          "logicalIdentifier": {
              "logicalId": "$logicalId"
          },
          "meta": {
              "versionId": "1",
              "profile": [
                  "https://fhir.nhs.uk/STU3/StructureDefinition/NRL-DocumentReference-1"
              ],
              "lastUpdated": "Tue, 23 Aug 2022 14:45:17 GMT"
          },
          "relatesTo": {
              "code": "$relatesToCode",
              "target": {
                  "reference": "$relatesToTarget",
                  "identifier": {
                      "value": "$relatesToIdentifier",
                      "system": "$relatesToSystem"
                  }
              }
          },
          "removed": false,
          "stability": {
              "coding": [
                  {
                      "code": "dynamic",
                      "system": "https://fhir.nhs.uk/STU3/CodeSystem/NRL-ContentStability-1",
                      "display": "Dynamic"
                  }
              ]
          },
          "status": "current",
          "type": {
              "code": "$typeCode",
              "display": "$typeDisplay"
          }
      }
      """
    And template DOCUMENT_REFERENCE
      """
      {
          "id": "$id",
          "status": "current",
          "type": {
              "coding": [
                  {
                      "code": "$typeCode",
                      "display": "$typeDisplay",
                      "system": "$typeSystem"
                  }
              ]
          },
          "category": [
              {
                  "coding": [
                      {
                          "code": "$classCode",
                          "display": "$classDisplay",
                          "system": "http://snomed.info/sct"
                      }
                  ]
              }
          ],
          "subject": {
              "identifier": {
                  "value": "$nhsNumber",
                  "system": "https://fhir.nhs.uk/Id/nhs-number"
              }
          },
          "date": "$indexed",
          "author": [
              {
                  "identifier": {
                      "value": "$asid",
                      "system": "https://fhir.nhs.uk/Id/nhsSpineASID"
                  }
              },
              {
                  "reference": "$author"
              }
          ],
          "custodian": {
              "identifier": {
                  "value": "$custodian",
                  "system": "https://fhir.nhs.uk/Id/ods-organization-code"
              }
          },
          "content": [
              {
                  "attachment": {
                      "url": "$attachmentUrl",
                      "contentType": "$attachmentContentType",
                      "creation": "$attachmentCreation"
                  },
                  "format": {
                      "code": "urn:nhs-ic:unstructured",
                "display": "Unstructured Document",
                "system": "https://fhir.nhs.uk/STU3/CodeSystem/NRL-FormatCode-1"
                  }
              }
          ],
          "context": {
              "practiceSetting": {
                  "coding": [
                      {
                          "code": "$practiceSettingCode",
                          "display": "$practiceSettingDisplay",
                          "system": "http://snomed.info/sct"
                      }
                  ]
              }
          },
          "resourceType": "DocumentReference",
          "relatesTo": [
              {
                  "code": "replaces",
                  "target": {
                      "identifier": {
                          "value": "$target"
                      }
                  }
              }
          ]
      }
      """
    And template DOCUMENT_REFERENCE_WITHOUT_CONTEXT
      """
      {
          "id": "$id",
          "status": "current",
          "type": {
              "coding": [
                  {
                      "code": "$typeCode",
                      "display": "$typeDisplay",
                      "system": "$typeSystem"
                  }
              ]
          },
          "category": [
              {
                  "coding": [
                      {
                          "code": "$classCode",
                          "display": "$classDisplay",
                          "system": "http://snomed.info/sct"
                      }
                  ]
              }
          ],
          "subject": {
              "identifier": {
                  "value": "$nhsNumber",
                  "system": "https://fhir.nhs.uk/Id/nhs-number"
              }
          },
          "date": "$indexed",
          "author": [
              {
                  "identifier": {
                      "value": "$asid",
                      "system": "https://fhir.nhs.uk/Id/nhsSpineASID"
                  }
              },
              {
                  "reference": "$author"
              }
          ],
          "custodian": {
              "identifier": {
                  "value": "$custodian",
                  "system": "https://fhir.nhs.uk/Id/ods-organization-code"
              }
          },
          "content": [
              {
                  "attachment": {
                      "url": "$attachmentUrl",
                      "contentType": "$attachmentContentType",
                      "creation": "$attachmentCreation"
                  },
                  "format": {
                      "code": "urn:nhs-ic:unstructured",
                      "display": "Unstructured Document",
                      "system": "https://fhir.nhs.uk/STU3/CodeSystem/NRL-FormatCode-1"
                  }
              }
          ],
          "resourceType": "DocumentReference",
          "relatesTo": [
              {
                  "code": "replaces",
                  "target": {
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

  Scenario: NRL can Create a DocumentReference from an NRL Document Pointer
    Given Producer "Data Sync" (Organisation ID "8FW23") is requesting to create Document Pointers
    And Producer "Data Sync" is registered in the system for application "DataShare" (ID "z00z-y11y-x22x") with pointer types
      | system                 | value     |
      | http://snomed.info/sct | 718377777 |
    And Producer "Data Sync" has the permission "audit-dates-from-payload"
    And Producer "Data Sync" has an NRL Document Pointer from NRL_DOCUMENT_POINTER template
      | property               | value                                                                                |
      | attachmentContentType  | application/pdf                                                                      |
      | attachmentCreation     | 2021-03-08T15:26:00+01:00                                                            |
      | attachmentUrl          | https://spine-proxy.national.ncrs.nhs.uk/p1.nhs.uk/MentalhealthCarePlanReportRGD.pdf |
      | author                 | https://directory.spineservices.nhs.uk/STU3/Organization/RAE                         |
      | classCode              | 734163000                                                                            |
      | classDisplay           | Care plan                                                                            |
      | custodian              | https://directory.spineservices.nhs.uk/STU3/Organization/8FW23                       |
      | indexed                | 2022-08-23T14:45:17+00:00                                                            |
      | lastModified           | Tue, 23 Aug 2022 14:45:17 GMT                                                        |
      | logicalId              | 341ec927-22f2-11ed-bd8d-000c290de2c0-58504e523530384b5851                            |
      | practiceSettingCode    | 310167005                                                                            |
      | practiceSettingDisplay | Urology service                                                                      |
      | relatesToCode          |                                                                                      |
      | relatesToIdentifier    |                                                                                      |
      | relatesToTarget        |                                                                                      |
      | relatesToSystem        |                                                                                      |
      | typeCode               | 718377777                                                                            |
      | typeDisplay            | Another Test data                                                                    |
    When Producer "Data Sync" uses "nrlf-converter" to convert NRL_DOCUMENT_POINTER with NHS Number "9278693472" and ASID "230811201350" into a DocumentReference according to the DOCUMENT_REFERENCE template
      | property               | value                                                                              |
      | id                     | 8FW23-341ec927-22f2-11ed-bd8d-000c290de2c0-58504e523530384b5851                    |
      | nhsNumber              | 9278693472                                                                         |
      | asid                   | 230811201350                                                                       |
      | attachmentContentType  | application/pdf                                                                    |
      | attachmentCreation     | 2021-03-08T15:26:00+01:00                                                          |
      | attachmentUrl          | ssp://spine-proxy.national.ncrs.nhs.uk/p1.nhs.uk/MentalhealthCarePlanReportRGD.pdf |
      | author                 | https://directory.spineservices.nhs.uk/STU3/Organization/RAE                       |
      | classCode              | 734163000                                                                          |
      | classDisplay           | Care plan                                                                          |
      | custodian              | 8FW23                                                                              |
      | indexed                | 2022-08-23T14:45:17+00:00                                                          |
      | lastModified           | Tue, 23 Aug 2022 14:45:17 GMT                                                      |
      | logicalId              | 341ec927-22f2-11ed-bd8d-000c290de2c0-58504e523530384b5851                          |
      | practiceSettingCode    | 310167005                                                                          |
      | practiceSettingDisplay | Urology service                                                                    |
      | typeCode               | 718377777                                                                          |
      | typeDisplay            | Another Test data                                                                  |
      | typeSystem             | http://snomed.info/sct                                                             |
    Then the operation is successful
    When Producer "Data Sync" creates a Document Reference from DOCUMENT_REFERENCE template
    Then the operation is successful
    And the status is 201
    And the response is an OperationOutcome according to the OUTCOME template with the below values
      | property          | value            |
      | issue_type        | informational    |
      | issue_level       | information      |
      | issue_code        | RESOURCE_CREATED |
      | issue_description | Resource created |
      | message           | Resource created |
    And Document Pointer "8FW23-341ec927-22f2-11ed-bd8d-000c290de2c0-58504e523530384b5851" exists
      | property    | value                                                           |
      | id          | 8FW23-341ec927-22f2-11ed-bd8d-000c290de2c0-58504e523530384b5851 |
      | nhs_number  | 9278693472                                                      |
      | producer_id | 8FW23                                                           |
      | type        | http://snomed.info/sct\|718377777                               |
      | source      | NRLF                                                            |
      | version     | 1                                                               |
      | updated_on  | NULL                                                            |
      | document    | <document>                                                      |
      | created_on  | <timestamp>                                                     |

  Scenario: NRL can Supersede a DocumentReference from an NRL Document Pointer
    Given Producer "Data Sync" (Organisation ID "8FW23") is requesting to create Document Pointers
    And Producer "Data Sync" is registered in the system for application "DataShare" (ID "z00z-y11y-x22x") with pointer types
      | system                 | value     |
      | http://snomed.info/sct | 718377777 |
    And a Document Pointer exists in the system with the below values for DOCUMENT_REFERENCE template
      | property               | value                                                                              |
      | id                     | 8FW23-e87816c5-1fc9-11ed-bd8d-000c290de2c0-58504e523530384b5851                    |
      | nhsNumber              | 9278693472                                                                         |
      | attachmentContentType  | application/pdf                                                                    |
      | attachmentCreation     | 2021-03-08T15:26:00+01:00                                                          |
      | attachmentUrl          | ssp://spine-proxy.national.ncrs.nhs.uk/p1.nhs.uk/MentalhealthCarePlanReportRGD.pdf |
      | author                 | https://directory.spineservices.nhs.uk/STU3/Organization/RAE                       |
      | classCode              | 734163000                                                                          |
      | classDisplay           | Care plan                                                                          |
      | custodian              | 8FW23                                                                              |
      | indexed                | 2022-08-23T14:45:17+00:00                                                          |
      | lastModified           | Tue, 23 Aug 2022 14:45:17 GMT                                                      |
      | logicalId              | 341ec927-22f2-11ed-bd8d-000c290de2c0-58504e523530384b5851                          |
      | practiceSettingCode    | 310167005                                                                          |
      | practiceSettingDisplay | Urology service                                                                    |
      | typeCode               | 718377777                                                                          |
      | typeDisplay            | Another Test data                                                                  |
      | typeSystem             | http://snomed.info/sct                                                             |
    And Producer "Data Sync" has an NRL Document Pointer from NRL_DOCUMENT_POINTER template
      | property               | value                                                                                                              |
      | attachmentContentType  | application/pdf                                                                                                    |
      | attachmentCreation     | 2021-03-08T15:26:00+01:00                                                                                          |
      | attachmentUrl          | https://spine-proxy.national.ncrs.nhs.uk/p1.nhs.uk/MentalhealthCarePlanReportRGD.pdf                               |
      | author                 | https://directory.spineservices.nhs.uk/STU3/Organization/RAE                                                       |
      | classCode              | 734163000                                                                                                          |
      | classDisplay           | Care plan                                                                                                          |
      | custodian              | https://directory.spineservices.nhs.uk/STU3/Organization/8FW23                                                     |
      | indexed                | 2022-08-23T14:45:17+00:00                                                                                          |
      | lastModified           | Tue, 23 Aug 2022 14:45:17 GMT                                                                                      |
      | logicalId              | 341ec927-22f2-11ed-bd8d-000c290de2c0-58504e523530384b5851                                                          |
      | practiceSettingCode    | 310167005                                                                                                          |
      | practiceSettingDisplay | Urology service                                                                                                    |
      | relatesToCode          | replaces                                                                                                           |
      | relatesToIdentifier    |                                                                                                                    |
      | relatesToTarget        | https://psis-sync.national.ncrs.nhs.uk/DocumentReference/e87816c5-1fc9-11ed-bd8d-000c290de2c0-58504e523530384b5851 |
      | relatesToSystem        |                                                                                                                    |
      | typeCode               | 718377777                                                                                                          |
      | typeDisplay            | Another Test data                                                                                                  |
    When Producer "Data Sync" uses "nrl-to-r4" to convert NRL_DOCUMENT_POINTER with NHS Number "9278693472" and ASID "230811201350" into a DocumentReference according to the DOCUMENT_REFERENCE template
      | property               | value                                                                              |
      | id                     | 8FW23-341ec927-22f2-11ed-bd8d-000c290de2c0-58504e523530384b5851                    |
      | nhsNumber              | 9278693472                                                                         |
      | asid                   | 230811201350                                                                       |
      | attachmentContentType  | application/pdf                                                                    |
      | attachmentCreation     | 2021-03-08T15:26:00+01:00                                                          |
      | attachmentUrl          | ssp://spine-proxy.national.ncrs.nhs.uk/p1.nhs.uk/MentalhealthCarePlanReportRGD.pdf |
      | author                 | https://directory.spineservices.nhs.uk/STU3/Organization/RAE                       |
      | classCode              | 734163000                                                                          |
      | classDisplay           | Care plan                                                                          |
      | custodian              | 8FW23                                                                              |
      | indexed                | 2022-08-23T14:45:17+00:00                                                          |
      | lastModified           | Tue, 23 Aug 2022 14:45:17 GMT                                                      |
      | logicalId              | 341ec927-22f2-11ed-bd8d-000c290de2c0-58504e523530384b5851                          |
      | practiceSettingCode    | 310167005                                                                          |
      | practiceSettingDisplay | Urology service                                                                    |
      | typeCode               | 718377777                                                                          |
      | typeDisplay            | Another Test data                                                                  |
      | typeSystem             | http://snomed.info/sct                                                             |
      | target                 | 8FW23-e87816c5-1fc9-11ed-bd8d-000c290de2c0-58504e523530384b5851                    |
    Then the operation is successful
    When Producer "Data Sync" creates a Document Reference from DOCUMENT_REFERENCE template
    Then the operation is successful
    And the status is 201
    And the response is an OperationOutcome according to the OUTCOME template with the below values
      | property          | value                                    |
      | issue_type        | informational                            |
      | issue_level       | information                              |
      | issue_code        | RESOURCE_SUPERSEDED                      |
      | issue_description | Resource created and Resource(s) deleted |
      | message           | Resource created and Resource(s) deleted |
    And Document Pointer "8FW23-341ec927-22f2-11ed-bd8d-000c290de2c0-58504e523530384b5851" exists
      | property    | value                                                           |
      | id          | 8FW23-341ec927-22f2-11ed-bd8d-000c290de2c0-58504e523530384b5851 |
      | nhs_number  | 9278693472                                                      |
      | producer_id | 8FW23                                                           |
      | type        | http://snomed.info/sct\|718377777                               |
      | source      | NRLF                                                            |
      | version     | 1                                                               |
      | updated_on  | NULL                                                            |
      | document    | <document>                                                      |
      | created_on  | <timestamp>                                                     |
    And Document Pointer "8FW23-e87816c5-1fc9-11ed-bd8d-000c290de2c0-58504e523530384b5851" does not exist

  Scenario: NRL can Supersede a DocumentReference from an NRL Document Pointer with Non Standard System URL
    Given Producer "Data Sync" (Organisation ID "8FW23") is requesting to create Document Pointers
    And Producer "Data Sync" is registered in the system for application "DataShare" (ID "z00z-y11y-x22x") with pointer types
      | system                 | value     |
      | http://snomed.info/sct | 718377777 |
    And a Document Pointer exists in the system with the below values for DOCUMENT_REFERENCE template
      | property               | value                                                                              |
      | id                     | 8FW23-e87816c5-1fc9-11ed-bd8d-000c290de2c0-58504e523530384b5851                    |
      | nhsNumber              | 9278693472                                                                         |
      | attachmentContentType  | application/pdf                                                                    |
      | attachmentCreation     | 2021-03-08T15:26:00+01:00                                                          |
      | attachmentUrl          | ssp://spine-proxy.national.ncrs.nhs.uk/p1.nhs.uk/MentalhealthCarePlanReportRGD.pdf |
      | author                 | https://directory.spineservices.nhs.uk/STU3/Organization/RAE                       |
      | classCode              | 734163000                                                                          |
      | classDisplay           | Care plan                                                                          |
      | custodian              | 8FW23                                                                              |
      | indexed                | 2022-08-23T14:45:17+00:00                                                          |
      | lastModified           | Tue, 23 Aug 2022 14:45:17 GMT                                                      |
      | logicalId              | 341ec927-22f2-11ed-bd8d-000c290de2c0-58504e523530384b5851                          |
      | practiceSettingCode    | 310167005                                                                          |
      | practiceSettingDisplay | Urology service                                                                    |
      | typeCode               | 718377777                                                                          |
      | typeDisplay            | Another Test data                                                                  |
      | typeSystem             | http://snomed.info/sct                                                             |
    And Producer "Data Sync" has an NRL Document Pointer from NRL_DOCUMENT_POINTER template
      | property               | value                                                                                                |
      | attachmentContentType  | application/pdf                                                                                      |
      | attachmentCreation     | 2021-03-08T15:26:00+01:00                                                                            |
      | attachmentUrl          | https://spine-proxy.national.ncrs.nhs.uk/p1.nhs.uk/MentalhealthCarePlanReportRGD.pdf                 |
      | author                 | https://directory.spineservices.nhs.uk/STU3/Organization/RAE                                         |
      | classCode              | 734163000                                                                                            |
      | classDisplay           | Care plan                                                                                            |
      | custodian              | https://directory.spineservices.nhs.uk/STU3/Organization/8FW23                                       |
      | indexed                | 2022-08-23T14:45:17+00:00                                                                            |
      | lastModified           | Tue, 23 Aug 2022 14:45:17 GMT                                                                        |
      | logicalId              | 341ec927-22f2-11ed-bd8d-000c290de2c0-58504e523530384b5851                                            |
      | practiceSettingCode    | 310167005                                                                                            |
      | practiceSettingDisplay | Urology service                                                                                      |
      | relatesToCode          | replaces                                                                                             |
      | relatesToIdentifier    |                                                                                                      |
      | relatesToTarget        | https://nhsengland.co.uk/DocumentReference/e87816c5-1fc9-11ed-bd8d-000c290de2c0-58504e523530384b5851 |
      | relatesToSystem        |                                                                                                      |
      | typeCode               | 718377777                                                                                            |
      | typeDisplay            | Another Test data                                                                                    |
    When Producer "Data Sync" uses "nrl-to-r4" to convert NRL_DOCUMENT_POINTER with NHS Number "9278693472" and ASID "230811201350" into a DocumentReference according to the DOCUMENT_REFERENCE template
      | property               | value                                                                              |
      | id                     | 8FW23-341ec927-22f2-11ed-bd8d-000c290de2c0-58504e523530384b5851                    |
      | nhsNumber              | 9278693472                                                                         |
      | asid                   | 230811201350                                                                       |
      | attachmentContentType  | application/pdf                                                                    |
      | attachmentCreation     | 2021-03-08T15:26:00+01:00                                                          |
      | attachmentUrl          | ssp://spine-proxy.national.ncrs.nhs.uk/p1.nhs.uk/MentalhealthCarePlanReportRGD.pdf |
      | author                 | https://directory.spineservices.nhs.uk/STU3/Organization/RAE                       |
      | classCode              | 734163000                                                                          |
      | classDisplay           | Care plan                                                                          |
      | custodian              | 8FW23                                                                              |
      | indexed                | 2022-08-23T14:45:17+00:00                                                          |
      | lastModified           | Tue, 23 Aug 2022 14:45:17 GMT                                                      |
      | logicalId              | 341ec927-22f2-11ed-bd8d-000c290de2c0-58504e523530384b5851                          |
      | practiceSettingCode    | 310167005                                                                          |
      | practiceSettingDisplay | Urology service                                                                    |
      | typeCode               | 718377777                                                                          |
      | typeDisplay            | Another Test data                                                                  |
      | typeSystem             | http://snomed.info/sct                                                             |
      | target                 | 8FW23-e87816c5-1fc9-11ed-bd8d-000c290de2c0-58504e523530384b5851                    |
    Then the operation is successful
    When Producer "Data Sync" creates a Document Reference from DOCUMENT_REFERENCE template
    Then the operation is successful
    And the status is 201
    And the response is an OperationOutcome according to the OUTCOME template with the below values
      | property          | value                                    |
      | issue_type        | informational                            |
      | issue_level       | information                              |
      | issue_code        | RESOURCE_SUPERSEDED                      |
      | issue_description | Resource created and Resource(s) deleted |
      | message           | Resource created and Resource(s) deleted |
    And Document Pointer "8FW23-341ec927-22f2-11ed-bd8d-000c290de2c0-58504e523530384b5851" exists
      | property    | value                                                           |
      | id          | 8FW23-341ec927-22f2-11ed-bd8d-000c290de2c0-58504e523530384b5851 |
      | nhs_number  | 9278693472                                                      |
      | producer_id | 8FW23                                                           |
      | type        | http://snomed.info/sct\|718377777                               |
      | source      | NRLF                                                            |
      | version     | 1                                                               |
      | updated_on  | NULL                                                            |
      | document    | <document>                                                      |
      | created_on  | <timestamp>                                                     |
    And Document Pointer "8FW23-e87816c5-1fc9-11ed-bd8d-000c290de2c0-58504e523530384b5851" does not exist

  Scenario: NRL can Supersede a DocumentReference from an NRL Document Pointer when target document does not exist
    Given Producer "Data Sync" (Organisation ID "8FW23") is requesting to create Document Pointers
    And Producer "Data Sync" is registered in the system for application "DataShare" (ID "z00z-y11y-x22x") with pointer types
      | system                 | value     |
      | http://snomed.info/sct | 718377777 |
    And Producer "Data Sync" has the permission "supersede-ignore-delete-fail"
    And Producer "Data Sync" has an NRL Document Pointer from NRL_DOCUMENT_POINTER template
      | property               | value                                                                                                              |
      | attachmentContentType  | application/pdf                                                                                                    |
      | attachmentCreation     | 2021-03-08T15:26:00+01:00                                                                                          |
      | attachmentUrl          | https://spine-proxy.national.ncrs.nhs.uk/p1.nhs.uk/MentalhealthCarePlanReportRGD.pdf                               |
      | author                 | https://directory.spineservices.nhs.uk/STU3/Organization/RAE                                                       |
      | classCode              | 734163000                                                                                                          |
      | classDisplay           | Care plan                                                                                                          |
      | custodian              | https://directory.spineservices.nhs.uk/STU3/Organization/8FW23                                                     |
      | indexed                | 2022-08-23T14:45:17+00:00                                                                                          |
      | lastModified           | Tue, 23 Aug 2022 14:45:17 GMT                                                                                      |
      | logicalId              | 341ec927-22f2-11ed-bd8d-000c290de2c0-58504e523530384b5851                                                          |
      | practiceSettingCode    | 310167005                                                                                                          |
      | practiceSettingDisplay | Urology service                                                                                                    |
      | relatesToCode          | replaces                                                                                                           |
      | relatesToIdentifier    |                                                                                                                    |
      | relatesToTarget        | https://psis-sync.national.ncrs.nhs.uk/DocumentReference/e87816c5-1fc9-11ed-bd8d-000c290de2c0-58504e523530384b5851 |
      | relatesToSystem        |                                                                                                                    |
      | typeCode               | 718377777                                                                                                          |
      | typeDisplay            | Another Test data                                                                                                  |
    When Producer "Data Sync" uses "nrl-to-r4" to convert NRL_DOCUMENT_POINTER with NHS Number "9278693472" and ASID "230811201350" into a DocumentReference according to the DOCUMENT_REFERENCE template
      | property               | value                                                                              |
      | id                     | 8FW23-341ec927-22f2-11ed-bd8d-000c290de2c0-58504e523530384b5851                    |
      | nhsNumber              | 9278693472                                                                         |
      | asid                   | 230811201350                                                                       |
      | attachmentContentType  | application/pdf                                                                    |
      | attachmentCreation     | 2021-03-08T15:26:00+01:00                                                          |
      | attachmentUrl          | ssp://spine-proxy.national.ncrs.nhs.uk/p1.nhs.uk/MentalhealthCarePlanReportRGD.pdf |
      | author                 | https://directory.spineservices.nhs.uk/STU3/Organization/RAE                       |
      | classCode              | 734163000                                                                          |
      | classDisplay           | Care plan                                                                          |
      | custodian              | 8FW23                                                                              |
      | indexed                | 2022-08-23T14:45:17+00:00                                                          |
      | lastModified           | Tue, 23 Aug 2022 14:45:17 GMT                                                      |
      | logicalId              | 341ec927-22f2-11ed-bd8d-000c290de2c0-58504e523530384b5851                          |
      | practiceSettingCode    | 310167005                                                                          |
      | practiceSettingDisplay | Urology service                                                                    |
      | typeCode               | 718377777                                                                          |
      | typeDisplay            | Another Test data                                                                  |
      | typeSystem             | http://snomed.info/sct                                                             |
      | target                 | 8FW23-e87816c5-1fc9-11ed-bd8d-000c290de2c0-58504e523530384b5851                    |
    Then the operation is successful
    When Producer "Data Sync" creates a Document Reference from DOCUMENT_REFERENCE template
    Then the operation is successful
    And the status is 201
    And the response is an OperationOutcome according to the OUTCOME template with the below values
      | property          | value            |
      | issue_type        | informational    |
      | issue_level       | information      |
      | issue_code        | RESOURCE_CREATED |
      | issue_description | Resource created |
      | message           | Resource created |
    And Document Pointer "8FW23-341ec927-22f2-11ed-bd8d-000c290de2c0-58504e523530384b5851" exists
      | property    | value                                                           |
      | id          | 8FW23-341ec927-22f2-11ed-bd8d-000c290de2c0-58504e523530384b5851 |
      | nhs_number  | 9278693472                                                      |
      | producer_id | 8FW23                                                           |
      | type        | http://snomed.info/sct\|718377777                               |
      | source      | NRLF                                                            |
      | version     | 1                                                               |
      | updated_on  | NULL                                                            |
      | document    | <document>                                                      |
      | created_on  | <timestamp>                                                     |
    And Document Pointer "8FW23-e87816c5-1fc9-11ed-bd8d-000c290de2c0-58504e523530384b5851" does not exist

  Scenario: NRL can Supersede a DocumentReference from an NRL Document Pointer with Target Identifier and System
    Given Producer "Data Sync" (Organisation ID "8FW23") is requesting to create Document Pointers
    And Producer "Data Sync" is registered in the system for application "DataShare" (ID "z00z-y11y-x22x") with pointer types
      | system                 | value     |
      | http://snomed.info/sct | 718377777 |
    And Producer "Data Sync" has the permission "supersede-ignore-delete-fail"
    And Producer "Data Sync" has an NRL Document Pointer from NRL_DOCUMENT_POINTER template
      | property               | value                                                                                |
      | attachmentContentType  | application/pdf                                                                      |
      | attachmentCreation     | 2021-03-08T15:26:00+01:00                                                            |
      | attachmentUrl          | https://spine-proxy.national.ncrs.nhs.uk/p1.nhs.uk/MentalhealthCarePlanReportRGD.pdf |
      | author                 | https://directory.spineservices.nhs.uk/STU3/Organization/RAE                         |
      | classCode              | 734163000                                                                            |
      | classDisplay           | Care plan                                                                            |
      | custodian              | https://directory.spineservices.nhs.uk/STU3/Organization/8FW23                       |
      | indexed                | 2022-08-23T14:45:17+00:00                                                            |
      | lastModified           | Tue, 23 Aug 2022 14:45:17 GMT                                                        |
      | logicalId              | 341ec927-22f2-11ed-bd8d-000c290de2c0-58504e523530384b5851                            |
      | practiceSettingCode    | 310167005                                                                            |
      | practiceSettingDisplay | Urology service                                                                      |
      | relatesToCode          | replaces                                                                             |
      | relatesToIdentifier    | urn:uuid:e87816c5-1fc9-11ed-bd8d-000c290de2c0-58504e523530384b5851                   |
      | relatesToTarget        |                                                                                      |
      | relatesToSystem        | urn:ietf:rfc:842                                                                     |
      | typeCode               | 718377777                                                                            |
      | typeDisplay            | Another Test data                                                                    |
    When Producer "Data Sync" uses "nrl-to-r4" to convert NRL_DOCUMENT_POINTER with NHS Number "9278693472" and ASID "230811201350" into a DocumentReference according to the DOCUMENT_REFERENCE template
      | property               | value                                                                              |
      | id                     | 8FW23-341ec927-22f2-11ed-bd8d-000c290de2c0-58504e523530384b5851                    |
      | nhsNumber              | 9278693472                                                                         |
      | asid                   | 230811201350                                                                       |
      | attachmentContentType  | application/pdf                                                                    |
      | attachmentCreation     | 2021-03-08T15:26:00+01:00                                                          |
      | attachmentUrl          | ssp://spine-proxy.national.ncrs.nhs.uk/p1.nhs.uk/MentalhealthCarePlanReportRGD.pdf |
      | author                 | https://directory.spineservices.nhs.uk/STU3/Organization/RAE                       |
      | classCode              | 734163000                                                                          |
      | classDisplay           | Care plan                                                                          |
      | custodian              | 8FW23                                                                              |
      | indexed                | 2022-08-23T14:45:17+00:00                                                          |
      | lastModified           | Tue, 23 Aug 2022 14:45:17 GMT                                                      |
      | logicalId              | 341ec927-22f2-11ed-bd8d-000c290de2c0-58504e523530384b5851                          |
      | practiceSettingCode    | 310167005                                                                          |
      | practiceSettingDisplay | Urology service                                                                    |
      | typeCode               | 718377777                                                                          |
      | typeDisplay            | Another Test data                                                                  |
      | typeSystem             | http://snomed.info/sct                                                             |
      | target                 | 8FW23-e87816c5-1fc9-11ed-bd8d-000c290de2c0-58504e523530384b5851                    |
    Then the operation is successful
    When Producer "Data Sync" creates a Document Reference from DOCUMENT_REFERENCE template
    Then the operation is successful
    And the status is 201
    And the response is an OperationOutcome according to the OUTCOME template with the below values
      | property          | value            |
      | issue_type        | informational    |
      | issue_level       | information      |
      | issue_code        | RESOURCE_CREATED |
      | issue_description | Resource created |
      | message           | Resource created |
    And Document Pointer "8FW23-341ec927-22f2-11ed-bd8d-000c290de2c0-58504e523530384b5851" exists
      | property    | value                                                           |
      | id          | 8FW23-341ec927-22f2-11ed-bd8d-000c290de2c0-58504e523530384b5851 |
      | nhs_number  | 9278693472                                                      |
      | producer_id | 8FW23                                                           |
      | type        | http://snomed.info/sct\|718377777                               |
      | source      | NRLF                                                            |
      | version     | 1                                                               |
      | updated_on  | NULL                                                            |
      | document    | <document>                                                      |
      | created_on  | <timestamp>                                                     |
    And Document Pointer "8FW23-e87816c5-1fc9-11ed-bd8d-000c290de2c0-58504e523530384b5851" does not exist

  Scenario: NRL can Create a DocumentReference from an NRL Document Pointer with No Attachment
    Given Producer "Data Sync" (Organisation ID "8FW23") is requesting to create Document Pointers
    And Producer "Data Sync" is registered in the system for application "DataShare" (ID "z00z-y11y-x22x") with pointer types
      | system                 | value     |
      | http://snomed.info/sct | 718377777 |
    And Producer "Data Sync" has the permission "audit-dates-from-payload"
    And Producer "Data Sync" has an NRL Document Pointer from NRL_DOCUMENT_POINTER template
      | property               | value                                                          |
      | attachmentContentType  | text/html                                                      |
      | attachmentCreation     | 2021-03-08T15:26:00+01:00                                      |
      | attachmentUrl          | https://spine-proxy.national.ncrs.nhs.uk/                      |
      | author                 | https://directory.spineservices.nhs.uk/STU3/Organization/RAE   |
      | classCode              | 734163000                                                      |
      | classDisplay           | Care plan                                                      |
      | custodian              | https://directory.spineservices.nhs.uk/STU3/Organization/8FW23 |
      | indexed                | 2022-08-23T14:45:17+00:00                                      |
      | lastModified           | Tue, 23 Aug 2022 14:45:17 GMT                                  |
      | logicalId              | a18af9ab-32b7-11ee-87e3-067a0214ca1a-58394e47453659524c33      |
      | practiceSettingCode    | 310167005                                                      |
      | practiceSettingDisplay | Urology service                                                |
      | relatesToCode          |                                                                |
      | relatesToIdentifier    |                                                                |
      | relatesToTarget        |                                                                |
      | relatesToSystem        |                                                                |
      | typeCode               | 718377777                                                      |
      | typeDisplay            | Another Test data                                              |
    When Producer "Data Sync" uses "nrlf-converter" to convert NRL_DOCUMENT_POINTER with NHS Number "9693893158" and ASID "230811201350" into a DocumentReference according to the DOCUMENT_REFERENCE template
      | property               | value                                                           |
      | id                     | 8FW23-a18af9ab-32b7-11ee-87e3-067a0214ca1a-58394e47453659524c33 |
      | nhsNumber              | 9693893158                                                      |
      | asid                   | 230811201350                                                    |
      | attachmentContentType  | text/html                                                       |
      | attachmentCreation     | 2021-03-08T15:26:00+01:00                                       |
      | attachmentUrl          | ssp://spine-proxy.national.ncrs.nhs.uk/                         |
      | author                 | https://directory.spineservices.nhs.uk/STU3/Organization/RAE    |
      | classCode              | 734163000                                                       |
      | classDisplay           | Care plan                                                       |
      | custodian              | 8FW23                                                           |
      | indexed                | 2022-08-23T14:45:17+00:00                                       |
      | lastModified           | Tue, 23 Aug 2022 14:45:17 GMT                                   |
      | logicalId              | a18af9ab-32b7-11ee-87e3-067a0214ca1a-58394e47453659524c33       |
      | practiceSettingCode    | 310167005                                                       |
      | practiceSettingDisplay | Urology service                                                 |
      | typeCode               | 718377777                                                       |
      | typeDisplay            | Another Test data                                               |
      | typeSystem             | http://snomed.info/sct                                          |
    Then the operation is successful
    When Producer "Data Sync" creates a Document Reference from DOCUMENT_REFERENCE template
    Then the operation is successful
    And the status is 201
    And the response is an OperationOutcome according to the OUTCOME template with the below values
      | property          | value            |
      | issue_type        | informational    |
      | issue_level       | information      |
      | issue_code        | RESOURCE_CREATED |
      | issue_description | Resource created |
      | message           | Resource created |
    And Document Pointer "8FW23-a18af9ab-32b7-11ee-87e3-067a0214ca1a-58394e47453659524c33" exists
      | property    | value                                                           |
      | id          | 8FW23-a18af9ab-32b7-11ee-87e3-067a0214ca1a-58394e47453659524c33 |
      | nhs_number  | 9693893158                                                      |
      | producer_id | 8FW23                                                           |
      | type        | http://snomed.info/sct\|718377777                               |
      | source      | NRLF                                                            |
      | version     | 1                                                               |
      | updated_on  | NULL                                                            |
      | document    | <document>                                                      |
      | created_on  | <timestamp>                                                     |

  Scenario: NRL can Create a DocumentReference from an NRL Document Pointer with No Context
    Given Producer "Data Sync" (Organisation ID "8FW23") is requesting to create Document Pointers
    And Producer "Data Sync" is registered in the system for application "DataShare" (ID "z00z-y11y-x22x") with pointer types
      | system                 | value     |
      | http://snomed.info/sct | 718377777 |
    And Producer "Data Sync" has the permission "audit-dates-from-payload"
    And Producer "Data Sync" has an NRL Document Pointer from NRL_DOCUMENT_POINTER_WITHOUT_CONTEXT template
      | property              | value                                                          |
      | attachmentContentType | text/html                                                      |
      | attachmentCreation    | 2021-03-08T15:26:00+01:00                                      |
      | attachmentUrl         | https://spine-proxy.national.ncrs.nhs.uk/                      |
      | author                | https://directory.spineservices.nhs.uk/STU3/Organization/RAE   |
      | classCode             | 734163000                                                      |
      | classDisplay          | Care plan                                                      |
      | custodian             | https://directory.spineservices.nhs.uk/STU3/Organization/8FW23 |
      | indexed               | 2022-08-23T14:45:17+00:00                                      |
      | lastModified          | Tue, 23 Aug 2022 14:45:17 GMT                                  |
      | logicalId             | 16f1ba23-32bc-11ee-87e3-067a0214ca1a-58394e47453659524c33      |
      | relatesToCode         |                                                                |
      | relatesToIdentifier   |                                                                |
      | relatesToTarget       |                                                                |
      | relatesToSystem       |                                                                |
      | typeCode              | 718377777                                                      |
      | typeDisplay           | Another Test data                                              |
    When Producer "Data Sync" uses "nrlf-converter" to convert NRL_DOCUMENT_POINTER_WITHOUT_CONTEXT with NHS Number "9693893158" and ASID "230811201350" into a DocumentReference according to the DOCUMENT_REFERENCE_WITHOUT_CONTEXT template
      | property              | value                                                           |
      | id                    | 8FW23-16f1ba23-32bc-11ee-87e3-067a0214ca1a-58394e47453659524c33 |
      | nhsNumber             | 9693893158                                                      |
      | asid                  | 230811201350                                                    |
      | attachmentContentType | text/html                                                       |
      | attachmentCreation    | 2021-03-08T15:26:00+01:00                                       |
      | attachmentUrl         | ssp://spine-proxy.national.ncrs.nhs.uk/                         |
      | author                | https://directory.spineservices.nhs.uk/STU3/Organization/RAE    |
      | classCode             | 734163000                                                       |
      | classDisplay          | Care plan                                                       |
      | custodian             | 8FW23                                                           |
      | indexed               | 2022-08-23T14:45:17+00:00                                       |
      | lastModified          | Tue, 23 Aug 2022 14:45:17 GMT                                   |
      | logicalId             | 16f1ba23-32bc-11ee-87e3-067a0214ca1a-58394e47453659524c33       |
      | typeCode              | 718377777                                                       |
      | typeDisplay           | Another Test data                                               |
      | typeSystem            | http://snomed.info/sct                                          |
    Then the operation is successful
    When Producer "Data Sync" creates a Document Reference from DOCUMENT_REFERENCE_WITHOUT_CONTEXT template
    Then the operation is successful
    And the status is 201
    And the response is an OperationOutcome according to the OUTCOME template with the below values
      | property          | value            |
      | issue_type        | informational    |
      | issue_level       | information      |
      | issue_code        | RESOURCE_CREATED |
      | issue_description | Resource created |
      | message           | Resource created |
    And Document Pointer "8FW23-16f1ba23-32bc-11ee-87e3-067a0214ca1a-58394e47453659524c33" exists
      | property    | value                                                           |
      | id          | 8FW23-16f1ba23-32bc-11ee-87e3-067a0214ca1a-58394e47453659524c33 |
      | nhs_number  | 9693893158                                                      |
      | producer_id | 8FW23                                                           |
      | type        | http://snomed.info/sct\|718377777                               |
      | source      | NRLF                                                            |
      | version     | 1                                                               |
      | updated_on  | NULL                                                            |
      | document    | <document>                                                      |
      | created_on  | <timestamp>                                                     |
