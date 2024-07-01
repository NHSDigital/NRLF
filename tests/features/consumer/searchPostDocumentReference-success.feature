Feature: Consumer - searchDocumentReference - Success Scenarios

  Scenario: Search for a DocumentReference by NHS Number
    Given the application 'DataShare' (ID 'z00z-y11y-x22x') is registered to access the API
    And the organisation 'RX898' is authorised to access pointer types:
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    And a DocumentReference resource exists with values:
      | property    | value                             |
      | id          | 8FW23-1234567890-SearchDocRefTest |
      | subject     | 9278693472                        |
      | status      | current                           |
      | type        | 736253002                         |
      | category    | 734163000                         |
      | contentType | application/pdf                   |
      | url         | https://example.org/my-doc.pdf    |
      | custodian   | 8FW23                             |
      | author      | 8FW23                             |
    When consumer 'RX898' searches for DocumentReferences with parameters:
      | parameter | value      |
      | subject   | 9278693472 |
    Then the response status code is 200
    And the response is a searchset Bundle
    And the Bundle has a self link matching 'DocumentReference?subject:identifier=https://fhir.nhs.uk/Id/nhs-number|9278693472'
    And the Bundle has a total of 1
    And the Bundle has 1 entry
    And the Bundle contains an DocumentReference with values
      | property    | value                             |
      | id          | 8FW23-1234567890-SearchDocRefTest |
      | subject     | 9278693472                        |
      | status      | current                           |
      | type        | 736253002                         |
      | category    | 734163000                         |
      | contentType | application/pdf                   |
      | url         | https://example.org/my-doc.pdf    |
      | custodian   | 8FW23                             |
      | author      | 8FW23                             |

  Scenario: Search for multiple DocumentReferences by NHS number
    Given the application 'DataShare' (ID 'z00z-y11y-x22x') is registered to access the API
    And the organisation 'RX898' is authorised to access pointer types:
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    And a DocumentReference resource exists with values:
      | property    | value                                 |
      | id          | X26-1111111111-SearchMultipleRefTest1 |
      | subject     | 9278693472                            |
      | status      | current                               |
      | type        | 736253002                             |
      | category    | 734163000                             |
      | contentType | application/pdf                       |
      | url         | https://example.org/my-doc-1.pdf      |
      | custodian   | X26                                   |
      | author      | X26                                   |
    And a DocumentReference resource exists with values:
      | property    | value                                 |
      | id          | X26-1111111111-SearchMultipleRefTest2 |
      | subject     | 9278693472                            |
      | status      | current                               |
      | type        | 736253002                             |
      | category    | 734163000                             |
      | contentType | application/pdf                       |
      | url         | https://example.org/my-doc-2.pdf      |
      | custodian   | X26                                   |
      | author      | X26                                   |
    And a DocumentReference resource exists with values:
      | property    | value                                             |
      | id          | X26-1111111111-SearchMultipleRefTestDifferentType |
      | subject     | 9278693472                                        |
      | status      | current                                           |
      | type        | 887701000000100                                   |
      | category    | 734163000                                         |
      | contentType | application/pdf                                   |
      | url         | https://example.org/my-doc-3.pdf                  |
      | custodian   | X26                                               |
      | author      | X26                                               |
    When consumer 'RX898' searches for DocumentReferences with parameters:
      | parameter | value      |
      | subject   | 9278693472 |
    Then the response status code is 200
    And the response is a searchset Bundle
    And the Bundle has a total of 2
    And the Bundle has 2 entries
    And the Bundle contains an DocumentReference with values
      | property    | value                                 |
      | id          | X26-1111111111-SearchMultipleRefTest1 |
      | subject     | 9278693472                            |
      | status      | current                               |
      | type        | 736253002                             |
      | category    | 734163000                             |
      | contentType | application/pdf                       |
      | url         | https://example.org/my-doc-1.pdf      |
      | custodian   | X26                                   |
      | author      | X26                                   |
    And the Bundle contains an DocumentReference with values
      | property    | value                                 |
      | id          | X26-1111111111-SearchMultipleRefTest2 |
      | subject     | 9278693472                            |
      | status      | current                               |
      | type        | 736253002                             |
      | category    | 734163000                             |
      | contentType | application/pdf                       |
      | url         | https://example.org/my-doc-2.pdf      |
      | custodian   | X26                                   |
      | author      | X26                                   |
    And the Bundle does not contain a DocumentReference with ID 'X26-1111111111-SearchMultipleRefTestDifferentType'

  Scenario: Search for multiple DocumentReferences by NHS number
    Given the application 'DataShare' (ID 'z00z-y11y-x22x') is registered to access the API
    And the organisation 'RX898' is authorised to access pointer types:
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    And a DocumentReference resource exists with values:
      | property    | value                                 |
      | id          | X26-1111111111-SearchMultipleRefTest1 |
      | subject     | 9278693472                            |
      | status      | current                               |
      | type        | 736253002                             |
      | category    | 734163000                             |
      | contentType | application/pdf                       |
      | url         | https://example.org/my-doc-1.pdf      |
      | custodian   | X26                                   |
      | author      | X26                                   |
    And a DocumentReference resource exists with values:
      | property    | value                                 |
      | id          | X26-1111111111-SearchMultipleRefTest2 |
      | subject     | 9278693472                            |
      | status      | current                               |
      | type        | 736253002                             |
      | category    | 734163000                             |
      | contentType | application/pdf                       |
      | url         | https://example.org/my-doc-2.pdf      |
      | custodian   | X26                                   |
      | author      | X26                                   |
    And a DocumentReference resource exists with values:
      | property    | value                                             |
      | id          | X26-1111111111-SearchMultipleRefTestDifferentType |
      | subject     | 9278693472                                        |
      | status      | current                                           |
      | type        | 887701000000100                                   |
      | category    | 734163000                                         |
      | contentType | application/pdf                                   |
      | url         | https://example.org/my-doc-3.pdf                  |
      | custodian   | X26                                               |
      | author      | X26                                               |
    When consumer 'RX898' searches for DocumentReferences with parameters:
      | parameter | value      |
      | subject   | 9278693472 |
    Then the response status code is 200
    And the response is a searchset Bundle
    And the Bundle has a total of 2
    And the Bundle has 2 entries
    And the Bundle contains an DocumentReference with values
      | property    | value                                 |
      | id          | X26-1111111111-SearchMultipleRefTest1 |
      | subject     | 9278693472                            |
      | status      | current                               |
      | type        | 736253002                             |
      | category    | 734163000                             |
      | contentType | application/pdf                       |
      | url         | https://example.org/my-doc-1.pdf      |
      | custodian   | X26                                   |
      | author      | X26                                   |
    And the Bundle contains an DocumentReference with values
      | property    | value                                 |
      | id          | X26-1111111111-SearchMultipleRefTest2 |
      | subject     | 9278693472                            |
      | status      | current                               |
      | type        | 736253002                             |
      | category    | 734163000                             |
      | contentType | application/pdf                       |
      | url         | https://example.org/my-doc-2.pdf      |
      | custodian   | X26                                   |
      | author      | X26                                   |
    And the Bundle does not contain a DocumentReference with ID 'X26-1111111111-SearchMultipleRefTestDifferentType'

# No pointers found
# Pointers exist but no permissions
# Search by custodian
