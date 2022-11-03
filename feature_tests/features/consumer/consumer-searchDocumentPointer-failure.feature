Feature: Basic Failure Scenarios where consumer is not able to search for Document Pointers
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

  Scenario: Empty results when searching for a Document Pointer when the consumer cant access existing document type
    Given a Document Pointer exists in the system with the below values
      | property    | value                             |
      | identifier  | 1114567890                        |
      | type        | 999253002                         |
      | custodian   | AMBULANCE PEOPLE TRUST IN THYSELF |
      | subject     | 9278693472                        |
      | contentType | application/pdf                   |
      | url         | https://example.org/my-doc.pdf    |
    And Consumer "TEST CONSUMER" has permission to search Document Pointers for
      | snomed_code | description                       |
      | 736253002   | Mental health crisis plan         |
    When "TEST CONSUMER" searches with query parameters
      | property      | value                           |
      | subject       | 9278693472                      |
    And "TEST CONSUMER" searches with the header values
      | property      | value                           |
      | type          | 736253002                       |
    Then the consumer search is made
    And the response is an empty bundle
