# Create care plan document reference
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
    And the response has a Location header
    And the Location header starts with '/nrl-producer-api/FHIR/R4/DocumentReference/ANGY1-'
    And the resource in the Location header exists with values:
      | property  | value                          |
      | subject   | 9278693472                     |
      | status    | current                        |
      | type      | 736253002                      |
      | category  | 734163000                      |
      | custodian | ANGY1                          |
      | author    | HAR1                           |
      | url       | https://example.org/my-doc.pdf |

# And the response is an OperationOutcome
# Create document reference with custodian suffix
# Create superseding document reference
# Create document reference with relatesTo - not code='replaces'
# Create document reference with relatesTo - multiple
# Create of each pointer type
# Create with content and contact details
# Create with contact details only
# Successfully create a Document Pointer with overridden created on date when producer has permission to set audit date
# SSP URL??
