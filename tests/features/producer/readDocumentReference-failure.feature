Feature: Producer - readDocumentReference - Failure Scenarios

  Scenario: Pointer not found
    Given the application 'DataShare' (ID 'z00z-y11y-x22x') is registered to access the API
    And the organisation 'RX898' is authorised to access pointer types:
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    When producer 'RX898' reads a DocumentReference with ID 'RX898-000000000-000000000'
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

  Scenario: No pointer types registered for organisation
    Given the application 'DataShare' (ID 'z00z-y11y-x22x') is registered to access the API
    When producer 'RX898' reads a DocumentReference with ID 'RX898-000000000-000000000'
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

  Scenario: No pointer types registered for organisation
    Given the application 'DataShare' (ID 'z00z-y11y-x22x') is registered to access the API
    And the organisation 'RX898'is authorised to access pointer types:
      | system | value |
    When producer 'RX898' reads a DocumentReference with ID 'RX898-000000000-000000000'
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

  Scenario: No permission file exists for organisation
    Given the application 'DataShare' (ID 'z00z-y11y-x22x') is registered to access the API
    When producer 'RX898' reads a DocumentReference with ID 'RX898-000000000-000000000'
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

  Scenario: Organisation attempts to access another organisation's pointer
    Given the application 'DataShare' (ID 'z00z-y11y-x22x') is registered to access the API
    And the organisation 'RX898' is authorised to access pointer types:
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    When producer 'RX898' reads a DocumentReference with ID 'X26-000000000-000000000'
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
              "code": "AUTHOR_CREDENTIALS_ERROR",
              "display": "Author credentials error"
            }
          ]
        },
        "diagnostics": "The requested DocumentReference cannot be read because it belongs to another organisation"
      }
      """

  Scenario: Read document reference by ID - custodian suffix mismatch
    Given the application 'DataShare' (ID 'z00z-y11y-x22x') is registered to access the API
    And the organisation 'RX898.001' is authorised to access pointer types:
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    And the organisation 'RX898.002' is authorised to access pointer types:
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    And a DocumentReference resource exists with values:
      | property    | value                                   |
      | id          | RX898.001-1234567890-CustSuffixMismatch |
      | subject     | 9999999999                              |
      | status      | current                                 |
      | type        | 736253002                               |
      | category    | 734163000                               |
      | contentType | application/pdf                         |
      | url         | https://example.org/my-doc.pdf          |
      | custodian   | RX898.001                               |
      | author      | X26                                     |
    When producer 'RX898.001' reads a DocumentReference with ID 'RX898.001-1234567890-CustSuffixMismatch'
    Then the response status code is 200
    When producer 'RX898.002' reads a DocumentReference with ID 'RX898.001-1234567890-CustSuffixMismatch'
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
              "code": "AUTHOR_CREDENTIALS_ERROR",
              "display": "Author credentials error"
            }
          ]
        },
        "diagnostics": "The requested DocumentReference cannot be read because it belongs to another organisation"
      }
      """
