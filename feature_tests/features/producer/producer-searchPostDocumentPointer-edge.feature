Feature: Producer Search Edge Case scenarios

  Background:
    Given template DOCUMENT
      """
      {
        "resourceType": "DocumentReference",
        "id": "$custodian-$identifier",
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
    And template INVALID_NHS_NUMBER_DOCUMENT
      """
      {
        "resourceType": "DocumentReference",
        "id": "$custodian-$identifier",
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

  Scenario: Successfully search for multiple Document Pointers with an empty request and ignores invalid data in results
    Given Producer "Aaron Court Mental Health NH" (Organisation ID "8FW23") is requesting to search Document Pointers
    And Producer "Aaron Court Mental Health NH" is registered in the system for application "DataShare" (ID "z00z-y11y-x22x") with pointer types
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    And a Document Pointer exists in the system with the below values for DOCUMENT template
      | property    | value                          |
      | identifier  | 1114567890                     |
      | type        | 736253002                      |
      | custodian   | 8FW23                          |
      | subject     | 9278693472                     |
      | contentType | application/pdf                |
      | url         | https://example.org/my-doc.pdf |
    And a Document Pointer exists in the system with the below values for DOCUMENT template
      | property    | value                            |
      | identifier  | 2224567890                       |
      | type        | 736253002                        |
      | custodian   | 8FW23                            |
      | subject     | 9278693472                       |
      | contentType | application/pdf                  |
      | url         | https://example.org/my-doc-2.pdf |
    And a Document Pointer exists in the system with the below values for DOCUMENT template
      | property    | value                            |
      | identifier  | 3334567890                       |
      | type        | 555553002                        |
      | custodian   | 8FW23                            |
      | subject     | 9278693472                       |
      | contentType | application/pdf                  |
      | url         | https://example.org/my-doc-2.pdf |
    And an invalid Document Pointer exists in the system with an invalid NHS Number and the below values for INVALID_NHS_NUMBER_DOCUMENT template
      | property    | value                          |
      | identifier  | 4444567890                     |
      | type        | 736253002                      |
      | custodian   | 8FW23                          |
      | subject     | 92786934721                    |
      | contentType | application/pdf                |
      | url         | https://example.org/my-doc.pdf |
    When Producer "Aaron Court Mental Health NH" searches by POST for Document References with body parameters:
      | property | value |
    Then the operation is successful
    And the response is a Bundle with 2 entries
    And the Bundle contains an Entry with the below values for DOCUMENT template
      | property    | value                          |
      | identifier  | 1114567890                     |
      | type        | 736253002                      |
      | custodian   | 8FW23                          |
      | subject     | 9278693472                     |
      | contentType | application/pdf                |
      | url         | https://example.org/my-doc.pdf |
    And the Bundle contains an Entry with the below values for DOCUMENT template
      | property    | value                            |
      | identifier  | 2224567890                       |
      | type        | 736253002                        |
      | custodian   | 8FW23                            |
      | subject     | 9278693472                       |
      | contentType | application/pdf                  |
      | url         | https://example.org/my-doc-2.pdf |
