Feature: Consumer - countDocumentReference - Failure Scenarios

  Scenario: No query parameters provided
    Given the application 'DataShare' (ID 'z00z-y11y-x22x') is registered to access the API
    And the organisation 'RX898' is authorised to access pointer types:
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    When consumer 'RX898' counts DocumentReferences with parameters:
      | parameter | value |
    Then the response status code is 400
    And the response is an OperationOutcome with 1 issue
    And the OperationOutcome contains the issue:
      """
      {
        "severity": "error",
        "code": "invalid",
        "details": {
          "coding": [{
            "system": "https://fhir.nhs.uk/ValueSet/Spine-ErrorOrWarningCode-1",
            "code": "INVALID_PARAMETER",
            "display": "Invalid parameter"
          }]
        },
        "diagnostics": "Invalid query parameter (subject:identifier: Field required)",
        "expression": ["subject:identifier"]
      }
      """

  Scenario: Invalid NHS number provided
    Given the application 'DataShare' (ID 'z00z-y11y-x22x') is registered to access the API
    And the organisation 'RX898' is authorised to access pointer types:
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    When consumer 'RX898' counts DocumentReferences with parameters:
      | parameter          | value                                  |
      | subject:identifier | https://fhir.nhs.uk/Id/nhs-number\|123 |
    Then the response status code is 400
    And the response is an OperationOutcome with 1 issue
    And the OperationOutcome contains the issue:
      """
      {
        "severity": "error",
        "code": "invalid",
        "details": {
          "coding": [{
            "system": "https://fhir.nhs.uk/ValueSet/Spine-ErrorOrWarningCode-1",
            "code": "INVALID_IDENTIFIER_VALUE",
            "display": "Invalid identifier value"
          }]
        },
        "diagnostics": "Invalid NHS number provided in the query parameters",
        "expression": ["subject:identifier"]
      }
      """

  Scenario: Organisation has no permissions
    Given the application 'DataShare' (ID 'z00z-y11y-x22x') is registered to access the API
    And the organisation 'RX898' is authorised to access pointer types:
      | system | value |
    When consumer 'RX898' counts DocumentReferences with parameters:
      | parameter          | value                                        |
      | subject:identifier | https://fhir.nhs.uk/Id/nhs-number\|999999999 |
    Then the response status code is 403
    And the response is an OperationOutcome with 1 issue
    And the OperationOutcome contains the issue:
      """
      {
        "severity": "error",
        "code": "forbidden",
        "details": {
          "coding": [{
            "system": "https://fhir.nhs.uk/ValueSet/Spine-ErrorOrWarningCode-1",
            "code": "ACCESS DENIED",
            "display": "Access has been denied to process this request"
          }]
        },
        "diagnostics": "Your organisation 'RX898' does not have permission to access this resource. Contact the onboarding team."
      }
      """

  Scenario: Organisation has no permissions in S3
    Given the application 'DataShare' (ID 'z00z-y11y-x22x') is registered to access the API
    And the organisation 'RX898' is authorised to access pointer types
      | system | value |
    When consumer 'RX898' counts DocumentReferences with parameters:
      | parameter          | value                                        |
      | subject:identifier | https://fhir.nhs.uk/Id/nhs-number\|999999999 |
    Then the response status code is 403
    And the response is an OperationOutcome with 1 issue
    And the OperationOutcome contains the issue:
      """
      {
        "severity": "error",
        "code": "forbidden",
        "details": {
          "coding": [{
            "system": "https://fhir.nhs.uk/ValueSet/Spine-ErrorOrWarningCode-1",
            "code": "ACCESS DENIED",
            "display": "Access has been denied to process this request"
          }]
        },
        "diagnostics": "Your organisation 'RX898' does not have permission to access this resource. Contact the onboarding team."
      }
      """
