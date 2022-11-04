Feature: Basic Success scenarios where producer is able to update a Document Pointer

  Background:
    Given template DOCUMENT:
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
         "status": "current"
      }
      """
    And a Document Pointer exists in the system with the below values
      | property    | value                                   |
      | identifier  | 1234567890                              |
      | type        | 736253002                               |
      | custodian   | ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL |
      | subject     | 9278693472                              |
      | contentType | application/pdf                         |
      | url         | https://example.org/my-doc.pdf          |

  Scenario Outline: Successfully update the mutable properties of a Document Pointer
    Given Producer "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL" has permission to update Document Pointers for
      | snomed_code | description                 |
      | 736253002   | "Mental health crisis plan" |
    When Producer "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL" updates a Document Reference "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL|1234567890" from DOCUMENT template
      | property    | value                                   |
      | identifier  | 1234567890                              |
      | status      | current                                 |
      | type        | 736253002                               |
      | custodian   | ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL |
      | subject     | 9278693472                              |
      | contentType | application/pdf                         |
      | <property>  | <value>                                 |
    Then the operation is successful
    And Document Pointer "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL|1234567890" exists
      | property    | value                                               |
      | id          | ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL\|1234567890 |
      | nhs_number  | 9278693472                                          |
      | producer_id | ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL             |
      | type        | https://snomed.info/ict\|736253002                  |
      | source      | NRLF                                                |
      | version     | 1                                                   |
      | document    | <<template>>                                        |
      | created_on  | <<timestamp>>                                       |
      | updated_on  | <<timestamp>>                                       |

    Examples:
      | property      | value                                           |
      | docStatus     | amended                                         |
      | author        | Organization/1XR                                |
      | authenticator | Organization/MHT01                              |
      | description   | Therapy Summary Document for Patient 9278693472 |
      | url           | https://example.org/different-doc.pdf           |
