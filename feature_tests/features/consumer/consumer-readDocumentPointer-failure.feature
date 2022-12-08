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
    Given Consumer "Yorkshire Ambulance Service" (Organisation ID "RX898") is requesting to read Document Pointers
    And Consumer "Yorkshire Ambulance Service" is registered in the system for application "DataShare" (ID "z00z-y11y-x22x") for document types
      | system                  | value     |
      | https://snomed.info/ict | 736253001 |
    And Consumer "Yorkshire Ambulance Service" has authorisation headers for application "DataShare" (ID "z00z-y11y-x22x")
    And a Document Pointer exists in the system with the below values for DOCUMENT template
      | property    | value                          |
      | identifier  | 1234567890                     |
      | type        | 736253002                      |
      | custodian   | 8FW23                          |
      | subject     | 9278693472                     |
      | contentType | application/pdf                |
      | url         | https://example.org/my-doc.pdf |
    When Consumer "Yorkshire Ambulance Service" reads an existing Document Reference "8FW23|1234567890"
    Then the operation is unsuccessful
    And the response contains error message "Item could not be found"

  Scenario: The Document Pointer does not exist
    Given Consumer "Yorkshire Ambulance Service" (Organisation ID "RX898") is requesting to read Document Pointers
    And Consumer "Yorkshire Ambulance Service" is registered in the system for application "DataShare" (ID "z00z-y11y-x22x") for document types
      | system                  | value     |
      | https://snomed.info/ict | 736253002 |
    And Consumer "Yorkshire Ambulance Service" has authorisation headers for application "DataShare" (ID "z00z-y11y-x22x")
    When Consumer "Yorkshire Ambulance Service" reads an existing Document Reference "8FW23|1234567890"
    Then the operation is unsuccessful
    And the response contains error message "Item could not be found"
