# Invalid document reference - structure
# Invalid document reference - required fields missing
# Invalid document reference - extra fields provided
# Invalid document reference - missing custodian identifier
# Invalid document reference - missing subject identifier
# Invalid document reference - invalid custodian system
# Invalid document reference - invalid subject system
# Invalid document reference - invalid relatesTo code
# Invalid document reference - invalid relatesTo target
# Invalid document reference - multiple type.coding
# Invalid document reference - invalid custodian suffix
Feature: Producer - createDocumentReference - Failure Scenarios

  Scenario: Producer and custodian ODS mismatch
    Given the application 'DataShare' (ID 'z00z-y11y-x22x') is registered to access the API
    And the organisation 'ANGY1' is authorised to access pointer types:
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    When producer 'ANGY1' creates a DocumentReference with values:
      | property  | value                          |
      | subject   | 9999999999                     |
      | status    | current                        |
      | type      | 736253002                      |
      | category  | 734163000                      |
      | custodian | N0TANGY                        |
      | author    | HAR1                           |
      | url       | https://example.org/my-doc.pdf |
    Then the response status code is 400
    And the response is an OperationOutcome with 1 issue
    And the OperationOutcome contains the issue:
      """
      {
        "severity": "error",
        "code": "invalid",
        "details": {
            "coding": [
            {
                "system": "https://fhir.nhs.uk/ValueSet/Spine-ErrorOrWarningCode-1",
                "code": "BAD_REQUEST",
                "display": "Bad request"
            }
            ]
        },
        "diagnostics": "The custodian of the provided DocumentReference does not match the expected ODS code for this organisation",
        "expression": [
            "custodian.identifier.value"
        ]
      }
      """

  Scenario: Invalid NHS number (correct length but not valid)
    Given the application 'DataShare' (ID 'z00z-y11y-x22x') is registered to access the API
    And the organisation 'ANGY1' is authorised to access pointer types:
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    When producer 'ANGY1' creates a DocumentReference with values:
      | property  | value                          |
      | subject   | 1234567890                     |
      | status    | current                        |
      | type      | 736253002                      |
      | category  | 734163000                      |
      | custodian | ANGY1                          |
      | author    | HAR1                           |
      | url       | https://example.org/my-doc.pdf |
    # NRL-765 known bug: this response is not handled properly, currently gives a 500
    # Then the response status code is 400
    Then the response is an OperationOutcome with 1 issue

  # And the OperationOutcome contains the issue:
  # """
  # {
  # "severity": "error",
  # "code": "informational",
  # "details": {
  # "coding": [
  # {
  # "system": "https://fhir.nhs.uk/ValueSet/Spine-ErrorOrWarningCode-1",
  # "code": "BAD_REQUEST",
  # "display": "Bad request"
  # }
  # ]
  # },
  # "diagnostics": "Invalid NHS number"
  # }
  # """
  Scenario: Invalid NHS number (valid number but wrong system)
    Given the application 'DataShare' (ID 'z00z-y11y-x22x') is registered to access the API
    And the organisation 'TSTCUS' is authorised to access pointer types:
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    When producer 'TSTCUS' requests creation of a DocumentReference with default test values except 'subject' is:
      """
      "subject": {
        "identifier": {
            "system": "https://fhir.nhs.uk/Id/not-nhs-number",
            "value": "9999999999"
        }
      }
      """
    Then the response status code is 400
    And the response is an OperationOutcome with 1 issue
    And the OperationOutcome contains the issue:
      """
      {
        "severity": "error",
        "code": "invalid",
        "details": {
            "coding": [
            {
                "system": "https://fhir.nhs.uk/ValueSet/Spine-ErrorOrWarningCode-1",
                "code": "INVALID_IDENTIFIER_SYSTEM",
                "display": "Invalid identifier system"
            }
            ]
        },
        "diagnostics": "Provided subject identifier system is not the NHS number system (expected 'https://fhir.nhs.uk/Id/nhs-number')",
        "expression": [
            "subject.identifier.system"
        ]
      }
      """

  # Invalid document reference - invalid custodian ID
  # Invalid document reference - invalid relatesTo target
  # Invalid document reference - invalid producer ID in relatesTo target
  Scenario: Unauthorised supersede - target belongs to a different custodian
    Given the application 'DataShare' (ID 'z00z-y11y-x22x') is registered to access the API
    And the organisation 'ANGY1' is authorised to access pointer types:
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    And a DocumentReference resource exists with values:
      | property    | value                           |
      | id          | N0TANGY-111-UnauthSupersedeTest |
      | subject     | 9278693472                      |
      | status      | current                         |
      | type        | 736253002                       |
      | category    | 734163000                       |
      | contentType | application/pdf                 |
      | url         | https://example.org/my-doc.pdf  |
      | custodian   | N0TANGY                         |
      | author      | HAR1                            |
    When producer 'ANGY1' creates a DocumentReference with values:
      | property   | value                           |
      | subject    | 9278693472                      |
      | status     | current                         |
      | type       | 736253002                       |
      | category   | 734163000                       |
      | custodian  | ANGY1                           |
      | author     | HAR1                            |
      | url        | https://example.org/newdoc.pdf  |
      | supercedes | N0TANGY-111-UnauthSupersedeTest |
    Then the response status code is 400
    And the response is an OperationOutcome with 1 issue
    And the OperationOutcome contains the issue:
      """
      {
        "severity": "error",
        "code": "invalid",
        "details": {
            "coding": [
              {
                "system": "https://fhir.nhs.uk/ValueSet/Spine-ErrorOrWarningCode-1",
                "code": "BAD_REQUEST",
                "display": "Bad request"
              }
            ]
        },
        "diagnostics": "The relatesTo target identifier value does not include the expected ODS code for this organisation",
        "expression": [
            "relatesTo[0].target.identifier.value"
        ]
      }
      """
    And the Document Reference 'N0TANGY-111-UnauthSupersedeTest' exists with values:
      | property    | value                           |
      | id          | N0TANGY-111-UnauthSupersedeTest |
      | subject     | 9278693472                      |
      | status      | current                         |
      | type        | 736253002                       |
      | category    | 734163000                       |
      | contentType | application/pdf                 |
      | url         | https://example.org/my-doc.pdf  |
      | custodian   | N0TANGY                         |

  # Invalid document reference - superseded document reference not found
  # Invalid document reference - superseded document reference NHS number mismatch
  # Invalid document reference - superseded document reference pointer type mismatch
  # Credentials - no pointer types allowed
  Scenario: Producer lacks permissions to create any pointer types
    Given the application 'DataShare' (ID 'z00z-y11y-x22x') is registered to access the API
    And the organisation 'ANGY1' is authorised to access pointer types:
      | system | value |
    When producer 'ANGY1' creates a DocumentReference with values:
      | property  | value                          |
      | subject   | 9999999999                     |
      | status    | current                        |
      | type      | 736253002                      |
      | category  | 734163000                      |
      | custodian | ANGY1                          |
      | author    | HAR1                           |
      | url       | https://example.org/my-doc.pdf |
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
        "diagnostics": "Your organisation 'ANGY1' does not have permission to access this resource. Contact the onboarding team."
      }
      """

  # Credentials - missing pointer type for create
  Scenario: Producer lacks the permission for the pointer type requested
    Given the application 'DataShare' (ID 'z00z-y11y-x22x') is registered to access the API
    And the organisation 'ANGY1' is authorised to access pointer types:
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    When producer 'ANGY1' creates a DocumentReference with values:
      | property  | value                          |
      | subject   | 9999999999                     |
      | status    | current                        |
      | type      | 1363501000000100               |
      | category  | 734163000                      |
      | custodian | ANGY1                          |
      | author    | HAR1                           |
      | url       | https://example.org/my-doc.pdf |
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
        "diagnostics": "The type of the provided DocumentReference is not in the list of allowed types for this organisation",
        "expression": [
          "type.coding[0].code"
        ]
      }
      """

  Scenario: Invalid category for type
    Given the application 'DataShare' (ID 'z00z-y11y-x22x') is registered to access the API
    And the organisation 'X26' is authorised to access pointer types:
      | system                 | value            |
      | http://snomed.info/sct | 1363501000000100 |
      | http://snomed.info/sct | 736253002        |
    When producer 'X26' creates a DocumentReference with values:
      | property  | value                          |
      | subject   | 9999999999                     |
      | status    | current                        |
      | type      | 1363501000000100               |
      | category  | 1102421000000108               |
      | custodian | X26                            |
      | author    | HAR1                           |
      | url       | https://example.org/my-doc.pdf |
    Then the response status code is 400
    And the response is an OperationOutcome with 1 issue
    And the OperationOutcome contains the issue:
      """
      {
        "severity": "error",
        "code": "invalid",
        "details": {
        "coding": [
        {
        "system": "https://fhir.nhs.uk/ValueSet/Spine-ErrorOrWarningCode-1",
        "code": "BAD_REQUEST",
        "display": "Bad request"
        }
        ]
        },
        "diagnostics": "The Category code of the provided document 'http://snomed.info/sct|1102421000000108' must match the allowed category for pointer type 'http://snomed.info/sct|736253002' with a category value of 'http://snomed.info/sct|734163000'",
        "expression": [
        "category.coding[0].code"
        ]
      }
      """

# Invalid document reference - invalid Type
# NRL-769 Known issue: Type display is not validated
# Scenario: Invalid type (valid code but wrong display value)
# Given the application 'DataShare' (ID 'z00z-y11y-x22x') is registered to access the API
# And the organisation 'TSTCUS' is authorised to access pointer types:
# | system                 | value            |
# | http://snomed.info/sct | 1363501000000100 |
# | http://snomed.info/sct | 736253002        |
# When producer 'TSTCUS' requests creation of a DocumentReference with default test values except 'type' is:
# """
# "type": {
# "coding": [
# {
# "system": "http://snomed.info/sct",
# "code": "736253002",
# "display": "Emergency Healthcare Plan"
# }
# ]
# }
# """
# Then the response status code is 400
# And the response is an OperationOutcome with 1 issue
# And the OperationOutcome contains the issue:
# """
# {
# "severity": "error",
# "code": "invalid",
# "details": {
# "coding": [
# {
# "system": "https://fhir.nhs.uk/ValueSet/Spine-ErrorOrWarningCode-1",
# "code": "BAD_REQUEST",
# "display": "Bad request"
# }
# ]
# },
# "diagnostics": "The display does not match the expected value for this type",
# "expression": [
# "type.coding.display"
# ]
# }
# """
# Invalid document reference - empty content[0].attachment.url
# Invalid document reference - create another producers document
# Invalid document reference - bad JSON
# Invalid document reference - invalid status (NRL-476 to ensure only 'current' is accepted)
# Scenario: Invalid document reference - invalid status
# Given the application 'DataShare' (ID 'z00z-y11y-x22x') is registered to access the API
# And the organisation 'ANGY1' is authorised to access pointer types:
# | system                 | value     |
# | http://snomed.info/sct | 736253002 |
# When producer 'ANGY1' creates a DocumentReference with values:
# | property  | value                          |
# | subject   | 9999999999                     |
# | status    | notarealStatus                 |
# | type      | 736253002                      |
# | category  | 734163000                      |
# | custodian | ANGY1                          |
# | author    | HAR1                           |
# | url       | https://example.org/my-doc.pdf |
# Then the response status code is 400
# And the response is an OperationOutcome with 1 issue
# And the OperationOutcome contains the issue:
# """
# {
# "severity": "error",
# "code": "forbidden",
# "details": {
# "coding": [
# {
# "system": "https://fhir.nhs.uk/ValueSet/Spine-ErrorOrWarningCode-1",
# "code": "AUTHOR_CREDENTIALS_ERROR",
# "display": "Author credentials error"
# }
# ]
# },
# "diagnostics": "The type of the provided DocumentReference is not in the list of allowed types for this organisation",
# "expression": [
# "type.coding[0].code"
# ]
# }
# """
# Invalid document reference - invalid author (NRL-474)
# Invalid document reference - invalid content (NRL-518)
# Invalid document reference - invalid context.related for an SSP url
# Invalid document reference - missing context.related for an SSP url
# Invalid document reference - invalid context.practiceSetting (NRL-519)
# Invalid document reference - invalid docStatus (NRL-477)
# Invalid document reference - duplicate keys
# Invalid document reference - duplicate relatesTo targets in URL
# Invalid document reference - supersede with duplicate error
# Invalid document reference - missing audit date when permission to set audit date
# Invalid document reference - SSP URL?
