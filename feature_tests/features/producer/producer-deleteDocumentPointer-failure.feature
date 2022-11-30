Feature: Failure scenarios where producer is unable to delete a Document Pointer

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

  Scenario: Unable to delete a Document Pointer when the Producer does not have permission
    Given a Document Pointer exists in the system with the below values:
      | property    | value                          |
      | identifier  | 1234567890                     |
      | type        | 736253002                      |
      | custodian   | AARON COURT MENTAL NH          |
      | subject     | 9278693472                     |
      | contentType | application/pdf                |
      | url         | https://example.org/my-doc.pdf |
    And Producer "AARON COURT MENTAL NH" has permission to delete Document Pointers for:
      | snomed_code | description                 |
      | 736253001   | "Mental health crisis plan" |
    When Producer "CUTHBERT'S CLOSE CARE HOME" deletes an existing Document Reference "CUTHBERT'S CLOSE CARE HOME|1234567890" as "Yorkshire Ambulance Service"
    Then the operation is unsuccessful
    And the response contains error message "Condition check failed - Forbidden"

  Scenario: Delete an existing current Document Pointer
    Given "Producer" "AARON COURT MENTAL NH" has permission to "delete" Document Pointers for:
      | snomed_code | description               |
      | 736253002   | Mental health crisis plan |
    When Producer "AARON COURT MENTAL NH" deletes an existing Document Reference "AARON COURT MENTAL NH|1234567890" as "Yorkshire Ambulance Service"
    Then the operation is unsuccessful
    And the response contains error message "Condition check failed - Forbidden"
