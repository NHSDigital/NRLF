Feature: Failure scenarios where consumer is unable to read a Document Pointer

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

  Scenario: Consumer permissions do not match the Document Pointer type
    Given a Document Pointer exists in the system with the below values
      | property    | value                          |
      | identifier  | 1234567890                     |
      | type        | 736253002                      |
      | custodian   | AARON COURT MENTAL NH          |
      | subject     | 9278693472                     |
      | contentType | application/pdf                |
      | url         | https://example.org/my-doc.pdf |
    And Consumer "WEST YORKSHIRE AMBULANCE SERVICE" has permission to read Document Pointers for
      | snomed_code | description |
      | 734163000   | Care plan   |
    When Consumer "WEST YORKSHIRE AMBULANCE SERVICE" reads an existing Document Reference "AARON COURT MENTAL NH|1234567890"
    Then the operation is unsuccessful
    And the response contains error message "Item could not be found"

  Scenario: The Document Pointer does not exist
    Given Consumer "WEST YORKSHIRE AMBULANCE SERVICE" has permission to read Document Pointers for
      | snomed_code | description               |
      | 736253002   | Mental health crisis plan |
    When Consumer "WEST YORKSHIRE AMBULANCE SERVICE" reads an existing Document Reference "AARON COURT MENTAL NH|1234567890"
    Then the operation is unsuccessful
    And the response contains error message "Item could not be found"
