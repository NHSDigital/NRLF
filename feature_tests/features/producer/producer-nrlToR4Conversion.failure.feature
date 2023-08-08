Feature: Producer NRL-to-R4 Conversion Failures

  Background:
    Given version "0.0.8" of "nrlf-converter" has been installed
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
          "status": "$status",
          "type": {
              "code": "$typeCode",
              "display": "$typeDisplay"
          }
      }
      """

  Scenario Outline: Cannot convert NRL to R4 because data contract has been broken
    Given Producer "Data Sync" (Organisation ID "8FW23") is requesting to create Document Pointers
    And Producer "Data Sync" has an NRL Document Pointer from NRL_DOCUMENT_POINTER template
      | property               | value                                                                                |
      | attachmentContentType  | application/pdf                                                                      |
      | attachmentCreation     | 2021-03-08T15:26:00+01:00                                                            |
      | attachmentUrl          | https://spine-proxy.national.ncrs.nhs.uk/p1.nhs.uk/MentalhealthCarePlanReportRGD.pdf |
      | author                 | https://directory.spineservices.nhs.uk/STU3/Organization/RAE                         |
      | classCode              | 734163000                                                                            |
      | classDisplay           | Care plan                                                                            |
      | custodian              | <custodian>                                                                          |
      | indexed                | 2022-08-23T14:45:17+00:00                                                            |
      | lastModified           | <lastModified>                                                                       |
      | logicalId              | <logicalId>                                                                          |
      | practiceSettingCode    | 310167005                                                                            |
      | practiceSettingDisplay | Urology service                                                                      |
      | relatesToCode          | <relatesToCode>                                                                      |
      | relatesToIdentifier    |                                                                                      |
      | relatesToTarget        | <relatesToTarget>                                                                    |
      | relatesToSystem        |                                                                                      |
      | status                 | <status>                                                                             |
      | typeCode               | <typeCode>                                                                           |
      | typeDisplay            | Another Test data                                                                    |
    When Producer "Data Sync" uses "nrlf-converter" to convert NRL_DOCUMENT_POINTER with NHS Number "9278693472" and ASID "230811201350" into a DocumentReference
    Then the operation is unsuccessful
    And the response is a "nrlf_converter.<error_type>" with error message
      """
      <error_message>
      """

    Examples:
      | custodian                                                      | relatesToCode | relatesToTarget | logicalId                                                 | status     | typeCode  | lastModified                  | error_type      | error_message                                                                                                                                                                                                                                                                                                                                                           |
      | https://directory.spineservices.nhs.uk/STU3/Organization/8FW23 | replaces      |                 | 341ec927-22f2-11ed-bd8d-000c290de2c0-58504e523530384b5851 | current    | 718377777 | Tue, 23 Aug 2022 14:45:17 GMT | ValidationError | 'FieldNotFound' encountered on 'DocumentPointer.relatesTo': Field 'RelatesTo.target' was expected but not provided.                                                                                                                                                                                                                                                     |
      | https://directory.spineservices.nhs.uk/STU3/Organization/8FW23 | replaces      | not-a-target    | 341ec927-22f2-11ed-bd8d-000c290de2c0-58504e523530384b5851 | current    | 718377777 | Tue, 23 Aug 2022 14:45:17 GMT | BadRelatesTo    | Could not parse an logicalId from either field 'reference' or 'identifier.value' in 'Reference(reference='not-a-target', identifier=None, display=None)' using patterns '['^https://psis-sync.national.ncrs.nhs.uk/DocumentReference/(?P<logical_id>.*), '^https://clinicals.spineservices.nhs.uk/DocumentReference/(?P<logical_id>.*), '^urn:uuid:(?P<logical_id>.*)]' |
      | https://directory.spineservices.nhs.uk/STU3/Organization/8FW23 |               |                 |                                                           | current    | 718377777 | Tue, 23 Aug 2022 14:45:17 GMT | ValidationError | Field 'DocumentPointer.logicalIdentifier' was expected but not provided.                                                                                                                                                                                                                                                                                                |
      | some/other/prefix/8FW23                                        |               |                 | 341ec927-22f2-11ed-bd8d-000c290de2c0-58504e523530384b5851 | current    | 718377777 | Tue, 23 Aug 2022 14:45:17 GMT | CustodianError  | Could not parse an ODS code from 'some/other/prefix/8FW23' using pattern '^https://directory.spineservices.nhs.uk/STU3/Organization/(?P<ods_code>\\w+)                                                                                                                                                                                                                  |
      | https://directory.spineservices.nhs.uk/STU3/Organization/8FW23 |               |                 | 341ec927-22f2-11ed-bd8d-000c290de2c0-58504e523530384b5851 | superseded | 718377777 | Tue, 23 Aug 2022 14:45:17 GMT | ValidationError | 'InvalidValue' encountered on 'DocumentPointer.status': Value 'superseded' was provided, but only 'current' is allowed.                                                                                                                                                                                                                                                 |
      | https://directory.spineservices.nhs.uk/STU3/Organization/8FW23 |               |                 | 341ec927-22f2-11ed-bd8d-000c290de2c0-58504e523530384b5851 | current    |           | Tue, 23 Aug 2022 14:45:17 GMT | ValidationError | 'FieldNotFound' encountered on 'DocumentPointer.type': Field 'Coding.code' was expected but not provided.                                                                                                                                                                                                                                                               |
