Feature: Producer - createDocumentReference - Success Scenarios

  Scenario: Successfully create a Document Pointer (care plan)
    Given the application 'DataShare' (ID 'z00z-y11y-x22x') is registered to access the API
    And the organisation 'ANGY1' is authorised to access pointer types:
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    When producer 'ANGY1' creates a DocumentReference with values:
      | property  | value                          |
      | subject   | 9278693472                     |
      | status    | current                        |
      | type      | 736253002                      |
      | category  | 734163000                      |
      | custodian | ANGY1                          |
      | author    | HAR1                           |
      | url       | https://example.org/my-doc.pdf |
    Then the response status code is 201
    And the response is an OperationOutcome with 1 issue
    And the OperationOutcome contains the issue:
      """
      {
      "severity": "information",
      "code": "informational",
      "details": {
      "coding": [
      {
      "system": "https://fhir.nhs.uk/ValueSet/NRL-ResponseCode",
      "code": "RESOURCE_CREATED",
      "display": "Resource created"
      }
      ]
      },
      "diagnostics": "The document has been created"
      }
      """
    And the response has a Location header
    And the Location header starts with '/producer/FHIR/R4/DocumentReference/ANGY1-'
    And the resource in the Location header exists with values:
      | property  | value                          |
      | subject   | 9278693472                     |
      | status    | current                        |
      | type      | 736253002                      |
      | category  | 734163000                      |
      | custodian | ANGY1                          |
      | author    | HAR1                           |
      | url       | https://example.org/my-doc.pdf |

  # # NRL-766 Resolve custodian suffix issues
  # Scenario: Successfully create a Document Pointer (care plan) with custodian suffix
  # Given the application 'DataShare' (ID 'z00z-y11y-x22x') is registered to access the API
  # And the organisation 'ANGY1.suffix001a' is authorised to access pointer types:
  # | system                 | value     |
  # | http://snomed.info/sct | 736253002 |
  # When producer 'ANGY1.suffix001a' creates a DocumentReference with values:
  # | property  | value                          |
  # | subject   | 9278693472                     |
  # | status    | current                        |
  # | type      | 736253002                      |
  # | category  | 734163000                      |
  # | custodian | ANGY1.suffix001a               |
  # | author    | HAR1                           |
  # | url       | https://example.org/my-doc.pdf |
  # Then the response status code is 201
  # And the response is an OperationOutcome with 1 issue
  # And the OperationOutcome contains the issue:
  # """
  # {
  # "severity": "information",
  # "code": "informational",
  # "details": {
  # "coding": [
  # {
  # "system": "https://fhir.nhs.uk/ValueSet/NRL-ResponseCode",
  # "code": "RESOURCE_CREATED",
  # "display": "Resource created"
  # }
  # ]
  # },
  # "diagnostics": "The document has been created"
  # }
  # """
  # And the response has a Location header
  # And the Location header starts with '/producer/FHIR/R4/DocumentReference/ANGY1'
  # And the resource in the Location header exists with values:
  # | property  | value                          |
  # | subject   | 9278693472                     |
  # | status    | current                        |
  # | type      | 736253002                      |
  # | category  | 734163000                      |
  # | custodian | ANGY1                          |
  # | author    | HAR1                           |
  # | url       | https://example.org/my-doc.pdf |
  # Create superseding document reference
  Scenario: Successfully create a Document Pointer that supercedes another
    Given the application 'DataShare' (ID 'z00z-y11y-x22x') is registered to access the API
    And the organisation 'ANGY1' is authorised to access pointer types:
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    And a DocumentReference resource exists with values:
      | property    | value                          |
      | id          | ANGY1-111-SupercedeDocRefTest1 |
      | subject     | 9278693472                     |
      | status      | current                        |
      | type        | 736253002                      |
      | category    | 734163000                      |
      | contentType | application/pdf                |
      | url         | https://example.org/my-doc.pdf |
      | custodian   | ANGY1                          |
      | author      | HAR1                           |
    When producer 'ANGY1' creates a DocumentReference with values:
      | property   | value                          |
      | subject    | 9278693472                     |
      | status     | current                        |
      | type       | 736253002                      |
      | category   | 734163000                      |
      | custodian  | ANGY1                          |
      | author     | HAR1                           |
      | url        | https://example.org/newdoc.pdf |
      | supercedes | ANGY1-111-SupercedeDocRefTest1 |
    Then the response status code is 201
    And the response is an OperationOutcome with 1 issue
    And the OperationOutcome contains the issue:
      """
      {
        "severity": "information",
        "code": "informational",
        "details": {
          "coding": [
            {
              "system": "https://fhir.nhs.uk/ValueSet/NRL-ResponseCode",
              "code": "RESOURCE_SUPERSEDED",
              "display": "Resource created and resource(s) deleted"
            }
          ]
        },
        "diagnostics": "The document has been superseded by a new version"
      }
      """
    And the response has a Location header
    And the Location header starts with '/producer/FHIR/R4/DocumentReference/ANGY1-'
    And the resource in the Location header exists with values:
      | property  | value                          |
      | subject   | 9278693472                     |
      | status    | current                        |
      | type      | 736253002                      |
      | category  | 734163000                      |
      | custodian | ANGY1                          |
      | author    | HAR1                           |
      | url       | https://example.org/newdoc.pdf |
    And the resource with id 'ANGY1-111-SupercedeDocRefTest1' does not exist

  # Create document reference with relatesTo - not code='replaces'
  # Create document reference with relatesTo - multiple
  Scenario Outline: Successfully create a document pointer of type
    Given the application 'DataShare' (ID 'z00z-y11y-x22x') is registered to access the API
    And the organisation 'ANGY1' is authorised to access pointer types:
      | system                 | value          |
      | http://snomed.info/sct | <pointer-type> |
    When producer 'ANGY1' creates a DocumentReference with values:
      | property  | value                          |
      | subject   | 9278693472                     |
      | status    | current                        |
      | type      | <pointer-type>                 |
      | category  | <pointer-category>             |
      | custodian | ANGY1                          |
      | author    | HAR1                           |
      | url       | https://example.org/my-doc.pdf |
    Then the response status code is 201
    And the response is an OperationOutcome with 1 issue
    And the OperationOutcome contains the issue:
      """
      {
      "severity": "information",
      "code": "informational",
      "details": {
      "coding": [
      {
      "system": "https://fhir.nhs.uk/ValueSet/NRL-ResponseCode",
      "code": "RESOURCE_CREATED",
      "display": "Resource created"
      }
      ]
      },
      "diagnostics": "The document has been created"
      }
      """
    And the response has a Location header
    And the Location header starts with '/producer/FHIR/R4/DocumentReference/ANGY1-'
    And the resource in the Location header exists with values:
      | property  | value                          |
      | subject   | 9278693472                     |
      | status    | current                        |
      | type      | <pointer-type>                 |
      | category  | <pointer-category>             |
      | custodian | ANGY1                          |
      | author    | HAR1                           |
      | url       | https://example.org/my-doc.pdf |

    Examples: Care Plans
      | pointer-type     | pointer-category | type-name                          |
      | 736253002        | 734163000        | MENTAL_HEALTH_PLAN                 |
      | 887701000000100  | 734163000        | EMERGENCY_HEALTHCARE_PLAN          |
      | 861421000000109  | 734163000        | EOL_COORDINATION_SUMMARY           |
      | 1382601000000107 | 734163000        | RESPECT_FORM                       |
      | 325691000000100  | 734163000        | CONTINGENCY_PLAN                   |
      | 736373009        | 734163000        | EOL_CARE_PLAN                      |
      | 16521000000101   | 734163000        | LLOYD_GEORGE_FOLDER                |
      | 736366004        | 734163000        | ADVANCED_CARE_PLAN                 |
      | 735324008        | 734163000        | TREATMENT_ESCALATION_PLAN          |
      | 2181441000000107 | 734163000        | PERSONALISED_CARE_AND_SUPPORT_PLAN |

    Examples: Observations
      | pointer-type     | pointer-category | type-name   |
      | 1363501000000100 | 1102421000000108 | NEWS2_CHART |

    Examples: Clinical Notes
      | pointer-type    | pointer-category | type-name      |
      | 824321000000109 | 823651000000106  | SUMMARY_RECORD |

# Create with content and contact details
# Create with contact details only
# Create with multiple attachments
# Successfully create a Document Pointer with overridden created on date when producer has permission to set audit date
# SSP URL??
