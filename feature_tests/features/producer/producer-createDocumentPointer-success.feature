Feature: Basic Success Scenarios where producer is able to create a Document Pointer

  Background:
    Given template DOCUMENT
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

  Scenario: Successfully create a Document Pointer of type Mental health crisis plan
    Given Producer "Aaron Court Mental Health NH" is requesting to create Document Pointers
    And Producer "Aaron Court Mental Health NH" is registered in the system for application "DataShare" for document types
      | system                  | value     |
      | https://snomed.info/ict | 736253002 |
    And Producer "Aaron Court Mental Health NH" has authorisation headers for application "DataShare"
    When Producer "Aaron Court Mental Health NH" creates a Document Reference from DOCUMENT template
      | property    | value                          |
      | identifier  | 1234567890                     |
      | type        | 736253002                      |
      | custodian   | Aaron Court Mental Health NH   |
      | subject     | 9278693472                     |
      | contentType | application/pdf                |
      | url         | https://example.org/my-doc.pdf |
    Then the operation is successful
    And Document Pointer "Aaron Court Mental Health NH|1234567890" exists
      | property    | value                                    |
      | id          | Aaron Court Mental Health NH\|1234567890 |
      | nhs_number  | 9278693472                               |
      | producer_id | Aaron Court Mental Health NH             |
      | type        | https://snomed.info/ict\|736253002       |
      | source      | NRLF                                     |
      | version     | 1                                        |
      | updated_on  | NULL                                     |
      | document    | <document>                               |
      | created_on  | <timestamp>                              |

  Scenario: Successfully create a Document Pointer of type End of life care coordination summary
    Given Producer "Aaron Court Mental Health NH" is requesting to create Document Pointers
    And Producer "Aaron Court Mental Health NH" is registered in the system for application "DataShare" for document types
      | system                  | value           |
      | https://snomed.info/ict | 861421000000109 |
    And Producer "Aaron Court Mental Health NH" has authorisation headers for application "DataShare"
    When Producer "Aaron Court Mental Health NH" creates a Document Reference from DOCUMENT template
      | property    | value                          |
      | identifier  | 1234567891                     |
      | type        | 861421000000109                |
      | custodian   | Aaron Court Mental Health NH   |
      | subject     | 2742179658                     |
      | contentType | application/pdf                |
      | url         | https://example.org/my-doc.pdf |
    Then the operation is successful
    And Document Pointer "Aaron Court Mental Health NH|1234567891" exists
      | property    | value                                    |
      | id          | Aaron Court Mental Health NH\|1234567891 |
      | nhs_number  | 2742179658                               |
      | producer_id | Aaron Court Mental Health NH             |
      | type        | https://snomed.info/ict\|861421000000109 |
      | source      | NRLF                                     |
      | version     | 1                                        |
      | updated_on  | NULL                                     |
      | document    | <document>                               |
      | created_on  | <timestamp>                              |
