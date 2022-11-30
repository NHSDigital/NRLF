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

  Scenario: Consumer permissions do not allow them to read requested Document Pointer type
    Given a Document Pointer exists in the system with the below values
      | property    | value                          |
      | identifier  | 1234567890                     |
      | type        | 736253002                      |
      | custodian   | AARON COURT MENTAL NH          |
      | subject     | 9278693472                     |
      | contentType | application/pdf                |
      | url         | https://example.org/my-doc.pdf |
    And the following organisation to application relationship exists
      | organisation                | application |
      | Yorkshire Ambulance Service | SCRa        |
    And "Yorkshire Ambulance Service" can access the following document types
      | system                  | value           |
      | https://snomed.info/ict | 861421000000109 |
    When Consumer "WEST YORKSHIRE AMBULANCE SERVICE" reads an existing Document Reference "AARON COURT MENTAL NH|1234567890" as "Yorkshire Ambulance Service"
      | property           | value            |
      | developer.app.id   | SCRa             |
      | developer.app.name | application name |
    Then the operation is unsuccessful
    And the response contains error message "Item could not be found"

  Scenario: The Document Pointer does not exist
    Given the following organisation to application relationship exists
      | organisation                | application |
      | Yorkshire Ambulance Service | SCRa        |
    And "Yorkshire Ambulance Service" can access the following document types
      | system                  | value           |
      | https://snomed.info/ict | 861421000000109 |
    When Consumer "WEST YORKSHIRE AMBULANCE SERVICE" reads an existing Document Reference "AARON COURT MENTAL NH|1234567890" as "Yorkshire Ambulance Service"
      | property           | value            |
      | developer.app.id   | SCRa             |
      | developer.app.name | application name |
    Then the operation is unsuccessful
    And the response contains error message "Item could not be found"
