Feature: Failure Scenarios where producer unable to create a Document Pointer

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

  Scenario: Requesting producer does not have permission to create another producers document
    Given Producer "Aaron Court Mental Health NH" is requesting to create Document Pointers
    And Producer "Aaron Court Mental Health NH" is registered in the system for application "DataShare" for document types
      | system                  | value           |
      | https://snomed.info/ict | 887701000000100 |
    And Producer "Aaron Court Mental Health NH" has authorisation headers for application "DataShare"
    When Producer "Aaron Court Mental Health NH" creates a Document Reference from DOCUMENT template
      | property    | value                          |
      | identifier  | 1234567892                     |
      | type        | 887701000000100                |
      | custodian   | CUTHBERT'S CLOSE CARE HOME     |
      | subject     | 2742179658                     |
      | contentType | application/pdf                |
      | url         | https://example.org/my-doc.pdf |
    Then the operation is unsuccessful
    And the response contains error message "Required permissions to create a document pointer are missing"

  Scenario Outline: Missing/invalid required params
    Given Producer "Aaron Court Mental Health NH" is requesting to create Document Pointers
    And Producer "Aaron Court Mental Health NH" is registered in the system for application "DataShare" for document types
      | system                  | value     |
      | https://snomed.info/ict | 736253002 |
    And Producer "Aaron Court Mental Health NH" has authorisation headers for application "DataShare"
    When Producer "Aaron Court Mental Health NH" creates a Document Reference from DOCUMENT template
      | property    | value                        |
      | identifier  | <identifier>                 |
      | type        | <type>                       |
      | custodian   | Aaron Court Mental Health NH |
      | subject     | <subject>                    |
      | contentType | application/pdf              |
      | url         | <url>                        |
    Then the operation is unsuccessful
    And the response contains error message "<error_message>"

    Examples:
      | identifier | type      | subject           | url                            | error_message                                                                                         |
      | 1234567890 | 736253002 | 45646             | https://example.org/my-doc.pdf | DocumentReference validation failure - Invalid nhs_number - Not a valid NHS Number: 45646             |
      | 1234567890 | 736253002 |                   | https://example.org/my-doc.pdf | DocumentReference validation failure - Invalid subject                                                |
      | 1234567890 | 736253002 | Device/9278693472 | https://example.org/my-doc.pdf | DocumentReference validation failure - Invalid nhs_number - Not a valid NHS Number: Device/9278693472 |

  Scenario: Duplicate Document Pointer
    Given Producer "Aaron Court Mental Health NH" is requesting to create Document Pointers
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
    When Producer "Aaron Court Mental Health NH" creates a Document Reference from DOCUMENT template
      | property    | value                          |
      | identifier  | 1234567890                     |
      | type        | 736253002                      |
      | custodian   | Aaron Court Mental Health NH   |
      | subject     | 9278693472                     |
      | contentType | application/pdf                |
      | url         | https://example.org/my-doc.pdf |
    Then the operation is unsuccessful
    And the response contains error message "Condition check failed - Duplicate rejected"
