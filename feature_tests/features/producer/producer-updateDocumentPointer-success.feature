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

  Scenario Outline: Successfully update the mutable properties of a Document Pointer with only one change
    Given Producer "Aaron Court Mental Health NH" is requesting to update Document Pointers
    And Producer "Aaron Court Mental Health NH" is registered in the system for application "DataShare" for document types
      | system                  | value     |
      | https://snomed.info/ict | 736253002 |
    And Producer "Aaron Court Mental Health NH" has authorisation headers for application "DataShare"
    And a Document Pointer exists in the system with the below values for DOCUMENT template
      | property    | value                          |
      | identifier  | 1234567890                     |
      | type        | 736253002                      |
      | custodian   | Aaron Court Mental Health NH   |
      | subject     | 9278693472                     |
      | contentType | application/pdf                |
      | url         | https://example.org/my-doc.pdf |
      | docStatus   | preliminary                    |
      | author      | Practitioner/xcda1             |
      | description | Physical                       |
    When Producer "Aaron Court Mental Health NH" updates Document Reference "Aaron Court Mental Health NH|1234567890" from DOCUMENT template
      | property    | value                        |
      | identifier  | 1234567890                   |
      | status      | current                      |
      | type        | 736253002                    |
      | custodian   | Aaron Court Mental Health NH |
      | subject     | 9278693472                   |
      | contentType | application/pdf              |
      | <property>  | <value>                      |
    Then the operation is successful
    And Document Pointer "Aaron Court Mental Health NH|1234567890" exists
      | property    | value                                    |
      | id          | Aaron Court Mental Health NH\|1234567890 |
      | nhs_number  | 9278693472                               |
      | producer_id | Aaron Court Mental Health NH             |
      | type        | https://snomed.info/ict\|736253002       |
      | source      | NRLF                                     |
      | version     | 1                                        |
      | document    | <document>                               |
      | created_on  | <timestamp>                              |
      | updated_on  | <timestamp>                              |

    Examples:
      | property    | value                                           |
      | docStatus   | amended                                         |
      | author      | Organization/1XR                                |
      | description | Therapy Summary Document for Patient 9278693472 |
      | url         | https://example.org/different-doc.pdf           |

  Scenario: Successfully update the mutable properties of a Document Pointer with multiple changes
    Given Producer "Aaron Court Mental Health NH" is requesting to update Document Pointers
    And Producer "Aaron Court Mental Health NH" is registered in the system for application "DataShare" for document types
      | system                  | value     |
      | https://snomed.info/ict | 736253002 |
    And Producer "Aaron Court Mental Health NH" has authorisation headers for application "DataShare"
    And a Document Pointer exists in the system with the below values for DOCUMENT template
      | property    | value                          |
      | identifier  | 1234567890                     |
      | type        | 736253002                      |
      | custodian   | Aaron Court Mental Health NH   |
      | subject     | 9278693472                     |
      | contentType | application/pdf                |
      | url         | https://example.org/my-doc.pdf |
      | docStatus   | preliminary                    |
      | author      | Practitioner/xcda1             |
      | description | Physical                       |
    When Producer "Aaron Court Mental Health NH" updates Document Reference "Aaron Court Mental Health NH|1234567890" from DOCUMENT template
      | property    | value                                           |
      | identifier  | 1234567890                                      |
      | status      | current                                         |
      | type        | 736253002                                       |
      | custodian   | Aaron Court Mental Health NH                    |
      | subject     | 9278693472                                      |
      | contentType | application/pdf                                 |
      | docStatus   | amended                                         |
      | author      | Organization/1XR                                |
      | description | Therapy Summary Document for Patient 9278693472 |
      | url         | https://example.org/different-doc.pdf           |
    Then the operation is successful
    And Document Pointer "Aaron Court Mental Health NH|1234567890" exists
      | property    | value                                    |
      | id          | Aaron Court Mental Health NH\|1234567890 |
      | nhs_number  | 9278693472                               |
      | producer_id | Aaron Court Mental Health NH             |
      | type        | https://snomed.info/ict\|736253002       |
      | source      | NRLF                                     |
      | version     | 1                                        |
      | document    | <document>                               |
      | created_on  | <timestamp>                              |
      | updated_on  | <timestamp>                              |
