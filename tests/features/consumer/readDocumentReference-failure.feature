# Invalid ID (X26|Something-)
Feature: Consumer - readDocumentReference - Failure Scenarios

  Scenario: Pointer not found
    Given the application 'DataShare' (ID 'z00z-y11y-x22x') is registered to access the API
    And the organisation 'RX898' is authorised to access pointer types:
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    When consumer 'RX898' reads a DocumentReference with ID 'X26-000000000-000000000'
    Then the response status code is 404
    And the response is an OperationOutcome with 1 issue
    And the OperationOutcome contains the issue:
      """
      {
        "severity": "error",
        "code": "not-found",
        "details": {
          "coding": [
            {
              "system": "https://fhir.nhs.uk/ValueSet/Spine-ErrorOrWarningCode-1",
              "code": "NO_RECORD_FOUND",
              "display": "No record found"
            }
          ]
        },
        "diagnostics": "The requested DocumentReference could not be found"
      }
      """

  # TODO: This scenario is not valid as the ID is not valid - additional validation required
  Scenario: Invalid ID in path parameters
    Given the application 'DataShare' (ID 'z00z-y11y-x22x') is registered to access the API
    And the organisation 'RX898' is authorised to access pointer types:
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    When consumer 'RX898' reads a DocumentReference with ID 'X26`DROP TABLE 'pointers';--Something-000000000-000000000'
    Then the response status code is 404
    And the response is an OperationOutcome with 1 issue
    And the OperationOutcome contains the issue:
      """
      {
        "severity": "error",
        "code": "not-found",
        "details": {
          "coding": [
            {
              "system": "https://fhir.nhs.uk/ValueSet/Spine-ErrorOrWarningCode-1",
              "code": "NO_RECORD_FOUND",
              "display": "No record found"
            }
          ]
        },
        "diagnostics": "The requested DocumentReference could not be found"
      }
      """

  Scenario: No permissions to access any resources
    Given the application 'DataShare' (ID 'z00z-y11y-x22x') is registered to access the API
    And the organisation 'RX898' is authorised to access pointer types:
      | system | value |
    When consumer 'RX898' reads a DocumentReference with ID 'X26-000000000-000000000'
    Then the response status code is 403
    And the response is an OperationOutcome with 1 issue
    And the OperationOutcome contains the issue:
      """
      {
        "severity": "error",
        "code": "forbidden",
        "details": {
          "coding": [
            {
              "system": "https://fhir.nhs.uk/ValueSet/Spine-ErrorOrWarningCode-1",
              "code": "ACCESS DENIED",
              "display": "Access has been denied to process this request"
            }
          ]
        },
        "diagnostics": "Your organisation 'RX898' does not have permission to access this resource. Contact the onboarding team."
      }
      """

  Scenario: No permissions to access specific pointer type
    Given the application 'DataShare' (ID 'z00z-y11y-x22x') is registered to access the API
    And the organisation 'RX898' is authorised to access pointer types:
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    And a DocumentReference resource exists with values:
      | property    | value                                  |
      | id          | 02V-1111111111-ReadDocRefNoAuthForType |
      | subject     | 9278693472                             |
      | status      | current                                |
      | type        | 887701000000100                        |
      | category    | 734163000                              |
      | contentType | application/pdf                        |
      | url         | https://example.org/my-doc.pdf         |
      | custodian   | 02V                                    |
      | author      | 02V                                    |
    When consumer 'RX898' reads a DocumentReference with ID '02V-1111111111-ReadDocRefNoAuthForType'
    Then the response status code is 403
    And the response is an OperationOutcome with 1 issue
    And the OperationOutcome contains the issue:
      """
      {
        "severity": "error",
        "code": "forbidden",
        "details": {
          "coding": [
            {
              "system": "https://fhir.nhs.uk/ValueSet/Spine-ErrorOrWarningCode-1",
              "code": "ACCESS DENIED",
              "display": "Access has been denied to process this request"
            }
          ]
        },
        "diagnostics": "The requested DocumentReference is not of a type that this organisation is allowed to access"
      }
      """

  Scenario: No permissions to access any pointers in S3
    Given the application 'DataShare' (ID 'z00z-y11y-x22x') is registered to access the API
    And the application is configured to lookup permissions from S3
    And the organisation 'RX898' is authorised in S3 to access pointer types:
      | system | value |
    When consumer 'RX898' reads a DocumentReference with ID 'X26-000000000-000000000'
    Then the response status code is 403
    And the response is an OperationOutcome with 1 issue
    And the OperationOutcome contains the issue:
      """
      {
        "severity": "error",
        "code": "forbidden",
        "details": {
          "coding": [
            {
              "system": "https://fhir.nhs.uk/ValueSet/Spine-ErrorOrWarningCode-1",
              "code": "ACCESS DENIED",
              "display": "Access has been denied to process this request"
            }
          ]
        },
        "diagnostics": "Your organisation 'RX898' does not have permission to access this resource. Contact the onboarding team."
      }
      """

  Scenario: No permissions to access specific pointer type in S3
    Given the application 'DataShare' (ID 'z00z-y11y-x22x') is registered to access the API
    And the application is configured to lookup permissions from S3
    And the organisation 'RX898' is authorised in S3 to access pointer types:
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    And a DocumentReference resource exists with values:
      | property    | value                                    |
      | id          | 02V-1111111111-ReadDocRefNoAuthForTypeS3 |
      | subject     | 9278693472                               |
      | status      | current                                  |
      | type        | 887701000000100                          |
      | category    | 734163000                                |
      | contentType | application/pdf                          |
      | url         | https://example.org/my-doc.pdf           |
      | custodian   | 02V                                      |
      | author      | 02V                                      |
    When consumer 'RX898' reads a DocumentReference with ID '02V-1111111111-ReadDocRefNoAuthForTypeS3'
    Then the response status code is 403
    And the response is an OperationOutcome with 1 issue
    And the OperationOutcome contains the issue:
      """
      {
        "severity": "error",
        "code": "forbidden",
        "details": {
          "coding": [
            {
              "system": "https://fhir.nhs.uk/ValueSet/Spine-ErrorOrWarningCode-1",
              "code": "ACCESS DENIED",
              "display": "Access has been denied to process this request"
            }
          ]
        },
        "diagnostics": "The requested DocumentReference is not of a type that this organisation is allowed to access"
      }
      """
