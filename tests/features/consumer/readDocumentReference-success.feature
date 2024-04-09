Feature: Consumer - readDocumentReference - Success Scenarios

  Scenario: Read document reference by ID - Requesting org is custodian
    Given the application 'DataShare' (ID 'z00z-y11y-x22x') is registered to access the API
    And the organisation 'RX898' is authorised to access pointer types:
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    And a DocumentReference resource exists with values:
      | property    | value                                    |
      | id          | RX898-9999999999-ReadDocRefSameCustodian |
      | subject     | 9999999999                               |
      | status      | current                                  |
      | type        | 736253002                                |
      | contentType | application/pdf                          |
      | url         | https://example.org/my-doc.pdf           |
      | custodian   | RX898                                    |
    When consumer 'RX898' reads a DocumentReference with ID 'RX898-9999999999-ReadDocRefSameCustodian'
    Then the response status code is 200
    And the response is a DocumentReference with JSON value:
      """
      {
        "resourceType": "DocumentReference",
        "id": "RX898-9999999999-ReadDocRefSameCustodian",
        "status": "current",
        "type": {
          "coding": [
            {
              "system": "http://snomed.info/sct",
              "code": "736253002"
            }
          ]
        },
        "subject": {
          "identifier": {
            "system": "https://fhir.nhs.uk/Id/nhs-number",
            "value": "9999999999"
          }
        },
        "custodian": {
          "identifier": {
            "system": "https://fhir.nhs.uk/Id/ods-organization-code",
            "value": "RX898"
          }
        },
        "content": [
          {
            "attachment": {
              "contentType": "application/pdf",
              "url": "https://example.org/my-doc.pdf"
            }
          }
        ]
      }
      """

  Scenario: Read document reference by ID - Requesting org is not custodian
    Given the application 'DataShare' (ID 'z00z-y11y-x22x') is registered to access the API
    And the organisation 'RX898' is authorised to access pointer types:
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    And a DocumentReference resource exists with values:
      | property    | value                                  |
      | id          | X26-9999999999-ReadDocRefDiffCustodian |
      | subject     | 9999999999                             |
      | status      | current                                |
      | type        | 736253002                              |
      | contentType | application/pdf                        |
      | url         | https://example.org/my-doc.pdf         |
      | custodian   | X26                                    |
    When consumer 'RX898' reads a DocumentReference with ID 'X26-9999999999-ReadDocRefDiffCustodian'
    Then the response status code is 200
    And the response is a DocumentReference with JSON value:
      """
      {
        "resourceType": "DocumentReference",
        "id": "X26-9999999999-ReadDocRefDiffCustodian",
        "status": "current",
        "type": {
          "coding": [
            {
              "system": "http://snomed.info/sct",
              "code": "736253002"
            }
          ]
        },
        "subject": {
          "identifier": {
            "system": "https://fhir.nhs.uk/Id/nhs-number",
            "value": "9999999999"
          }
        },
        "custodian": {
          "identifier": {
            "system": "https://fhir.nhs.uk/Id/ods-organization-code",
            "value": "X26"
          }
        },
        "content": [
          {
            "attachment": {
              "contentType": "application/pdf",
              "url": "https://example.org/my-doc.pdf"
            }
          }
        ]
      }
      """

  Scenario: Read document reference by ID - urlencoded
    Given the application 'DataShare' (ID 'z00z-y11y-x22x') is registered to access the API
    And the organisation 'RX898' is authorised to access pointer types:
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    And a DocumentReference resource exists with values:
      | property    | value                                      |
      | id          | RX898\|001-1234567890-ReadDocRefUrlEncoded |
      | subject     | 9999999999                                 |
      | status      | current                                    |
      | type        | 736253002                                  |
      | contentType | application/pdf                            |
      | url         | https://example.org/my-doc.pdf             |
      | custodian   | RX898\|001                                 |
    When consumer 'RX898' reads a DocumentReference with ID 'RX898%7C001-1234567890-ReadDocRefUrlEncoded'
    Then the response status code is 200
