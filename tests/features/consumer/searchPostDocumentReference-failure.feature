Feature: Consumer - searchDocumentReference - Failure Scenarios

  Scenario: Search fails to return a bundle when extra keys are found
    Given the application 'DataShare' (ID 'z00z-y11y-x22x') is registered to access the API
    And the organisation 'RX898' is authorised to access pointer types:
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    When consumer 'RX898' searches for DocumentReferences using POST with request body:
      | key     | value      |
      | subject | 9278693472 |
      | extra   | parameter  |
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
            "code": "MESSAGE_NOT_WELL_FORMED",
            "display": "Message not well formed"
          }]
        },
        "diagnostics": "Request body could not be parsed (extra: Extra inputs are not permitted)",
        "expression": ["extra"]
      }
      """

  Scenario: Search fails to return a bundle when no subject:identifier is provided
    Given the application 'DataShare' (ID 'z00z-y11y-x22x') is registered to access the API
    And the organisation 'RX898' is authorised to access pointer types:
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    When consumer 'RX898' searches for DocumentReferences using POST with request body:
      | key | value |
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
            "code": "MESSAGE_NOT_WELL_FORMED",
            "display": "Message not well formed"
          }]
        },
        "diagnostics": "Request body could not be parsed (subject:identifier: Field required)",
        "expression": ["subject:identifier"]
      }
      """

  Scenario: Search rejects request with type system they are not allowed to use
    Given the application 'DataShare' (ID 'z00z-y11y-x22x') is registered to access the API
    And the organisation 'RX898' is authorised to access pointer types:
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    When consumer 'RX898' searches for DocumentReferences using POST with request body:
      | key     | value                                |
      | subject | 9278693472                           |
      | type    | http://incorrect.info/sct\|736253002 |
    Then the response status code is 400
    And the response is an OperationOutcome with 1 issue
    And the OperationOutcome contains the issue:
      """
      {
        "severity": "error",
        "code": "code-invalid",
        "details": {
          "coding": [{
            "system": "https://fhir.nhs.uk/ValueSet/Spine-ErrorOrWarningCode-1",
            "code": "INVALID_CODE_SYSTEM",
            "display": "Invalid code system"
          }]
        },
        "diagnostics": "Invalid type (The provided type system does not match the allowed types for this organisation)",
        "expression": ["type"]
      }
      """

  Scenario: Search rejects request when the NHS number provided is invalid
    Given the application 'DataShare' (ID 'z00z-y11y-x22x') is registered to access the API
    And the organisation 'RX898' is authorised to access pointer types:
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    When consumer 'RX898' searches for DocumentReferences using POST with request body:
      | key     | value |
      | subject | 123   |
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
            "code": "INVALID_NHS_NUMBER",
            "display": "Invalid NHS number"
          }]
        },
        "diagnostics": "A valid NHS number is required to search for document references",
        "expression": ["subject:identifier"]
      }
      """

  Scenario: Search rejects request if the organisation has no registered pointer types
    Given the application 'DataShare' (ID 'z00z-y11y-x22x') is registered to access the API
    And the organisation 'RX898' is authorised to access pointer types:
      | system | value |
    When consumer 'RX898' searches for DocumentReferences using POST with request body:
      | key     | value      |
      | subject | 9278693472 |
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

  Scenario: Search returns 403 if no permissions
    Given the application 'DataShare' (ID 'z00z-y11y-x22x') is registered to access the API
    And a DocumentReference resource exists with values:
      | property    | value                             |
      | id          | 8FW23-1114567890-SearchDocRefTest |
      | subject     | 9278693472                        |
      | status      | current                           |
      | type        | 736253002                         |
      | category    | 734163000                         |
      | contentType | application/pdf                   |
      | url         | https://example.org/my-doc.pdf    |
      | custodian   | 8FW23                             |
      | author      | 8FW23                             |
    When consumer 'X26' searches for DocumentReferences using POST with request body:
      | key     | value      |
      | subject | 9278693472 |
      | type    | 736253002  |
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
        "diagnostics": "Your organisation 'X26' does not have permission to access this resource. Contact the onboarding team."
      }
      """

  Scenario: Search rejects request if the organisation has no registered pointer types
    Given the application 'DataShare' (ID 'z00z-y11y-x22x') is registered to access the API
    When consumer 'RX898' searches for DocumentReferences using POST with request body:
      | key     | value      |
      | subject | 9278693472 |
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
