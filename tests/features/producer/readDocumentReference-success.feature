# Read document reference by ID
# Read document reference by ID - urlencoded
Feature: Producer - readDocumentReference - Success Scenarios

  Scenario: Read document reference by ID
    Given the application 'DataShare' (ID 'z00z-y11y-x22x') is registered to access the API
    And the organisation 'RX898' is authorised to access pointer types:
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    And a DocumentReference resource exists with values:
      | property    | value                               |
      | id          | RX898-9999999999-ReadDocRefSameCust |
      | subject     | 9999999999                          |
      | status      | current                             |
      | type        | 736253002                           |
      | category    | 734163000                           |
      | contentType | application/pdf                     |
      | url         | https://example.org/my-doc.pdf      |
      | custodian   | RX898                               |
      | author      | HAR1                                |
    When producer 'RX898' reads a DocumentReference with ID 'RX898-9999999999-ReadDocRefSameCust'
    Then the response status code is 200
    And the response is a DocumentReference with JSON value:
      """
      {
        "resourceType": "DocumentReference",
        "id": "RX898-9999999999-ReadDocRefSameCust",
        "status": "current",
        "type": {
          "coding": [
            {
              "system": "http://snomed.info/sct",
              "code": "736253002"
            }
          ]
        },
        "category": [
          {
            "coding": [
              {
                "system": "http://snomed.info/sct",
                "code": "734163000",
                "display": "Care plan"
              }
            ]
          }
        ],
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
        "author": [
          {
            "identifier": {
              "system": "https://fhir.nhs.uk/Id/ods-organization-code",
              "value": "HAR1"
            }
          }
        ],
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

  Scenario: Read document reference by ID - S3 permissions
    Given the application 'DataShare' (ID 'z00z-y11y-x22x') is registered to access the API
    And the application is configured to lookup permissions from S3
    And the organisation 'RX898' is authorised in S3 to access pointer types:
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    And a DocumentReference resource exists with values:
      | property    | value                               |
      | id          | RX898-9999999999-ReadDocRefSameCust |
      | subject     | 9999999999                          |
      | status      | current                             |
      | type        | 736253002                           |
      | category    | 734163000                           |
      | contentType | application/pdf                     |
      | url         | https://example.org/my-doc.pdf      |
      | custodian   | RX898                               |
      | author      | HAR1                                |
    When producer 'RX898' reads a DocumentReference with ID 'RX898-9999999999-ReadDocRefSameCust'
    Then the response status code is 200
    And the response is a DocumentReference with JSON value:
      """
      {
        "resourceType": "DocumentReference",
        "id": "RX898-9999999999-ReadDocRefSameCust",
        "status": "current",
        "type": {
          "coding": [
            {
              "system": "http://snomed.info/sct",
              "code": "736253002"
            }
          ]
        },
        "category": [
          {
            "coding": [
              {
                "system": "http://snomed.info/sct",
                "code": "734163000",
                "display": "Care plan"
              }
            ]
          }
        ],
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
        "author": [
          {
            "identifier": {
              "system": "https://fhir.nhs.uk/Id/ods-organization-code",
              "value": "HAR1"
            }
          }
        ],
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

  Scenario: Read document reference by ID - custodian suffix
    Given the application 'DataShare' (ID 'z00z-y11y-x22x') is registered to access the API
    And the organisation 'RX898.001' is authorised to access pointer types:
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    And the organisation 'RX898.002' is authorised to access pointer types:
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    And a DocumentReference resource exists with values:
      | property    | value                                     |
      | id          | RX898.001-1234567890-ReadDocRefCustSuffix |
      | subject     | 9999999999                                |
      | status      | current                                   |
      | type        | 736253002                                 |
      | category    | 734163000                                 |
      | contentType | application/pdf                           |
      | url         | https://example.org/my-doc.pdf            |
      | custodian   | RX898.001                                 |
      | author      | HAR1                                      |
    When producer 'RX898.001' reads a DocumentReference with ID 'RX898.001-1234567890-ReadDocRefCustSuffix'
    Then the response status code is 200
