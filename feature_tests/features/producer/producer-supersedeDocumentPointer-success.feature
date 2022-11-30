Feature: Success Scenarios where producer unable to supersede Document Pointers

  Background:
    Given template DOCUMENT
      """
      {
        "resourceType": "DocumentReference",
        "id": "$identifier",
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
              "system": "https://snomed.info/ict",
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

  Scenario: Supersede multiple Document Pointers
    Given a Document Pointer exists in the system with the below values
      | property    | value                                               |
      | identifier  | ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL\|1234567890 |
      | type        | 736253002                                           |
      | custodian   | ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL             |
      | subject     | 9278693472                                          |
      | contentType | application/pdf                                     |
      | url         | https://example.org/my-doc.pdf                      |
    And a Document Pointer exists in the system with the below values
      | property    | value                                               |
      | identifier  | ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL\|1234567891 |
      | type        | 736253002                                           |
      | custodian   | ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL             |
      | subject     | 9278693472                                          |
      | contentType | application/pdf                                     |
      | url         | https://example.org/my-doc.pdf                      |
    And Producer "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL" has permission to create Document Pointers for
      | snomed_code | description               |
      | 736253002   | Mental health crisis plan |
    When Producer "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL" creates a Document Reference from DOCUMENT template as "Yorkshire Ambulance Service"
      | property    | value                                               |
      | identifier  | ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL\|1234567892 |
      | target      | ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL\|1234567890 |
      | target      | ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL\|1234567891 |
      | type        | 736253002                                           |
      | custodian   | ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL             |
      | subject     | 9278693472                                          |
      | contentType | application/pdf                                     |
      | url         | https://example.org/my-doc.pdf                      |
    Then the operation is successful
    And Document Pointer "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL|1234567892" exists
      | property    | value                                               |
      | id          | ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL\|1234567892 |
      | nhs_number  | 9278693472                                          |
      | producer_id | ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL             |
      | type        | https://snomed.info/ict\|736253002                  |
      | source      | NRLF                                                |
      | version     | 1                                                   |
      | updated_on  | NULL                                                |
      | document    | <<template>>                                        |
      | created_on  | <<timestamp>>                                       |
    And Document Pointer "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL|1234567890" does not exist
    And Document Pointer "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL|1234567891" does not exist
