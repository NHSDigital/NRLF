Feature: Producer - searchDocumentReference - Success Scenarios

  Scenario: Search for DocumentReferences by NHS number
    Given the application 'DataShare' (ID 'z00z-y11y-x22x') is registered to access the API
    And the organisation 'RX898' is authorised to access pointer types:
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    And a DocumentReference resource exists with values:
      | property    | value                                 |
      | id          | RX898-1111111111-SearchNHSDocRefTest1 |
      | subject     | 9278693472                            |
      | status      | current                               |
      | type        | 736253002                             |
      | category    | 734163000                             |
      | contentType | application/pdf                       |
      | url         | https://example.org/my-doc.pdf        |
      | custodian   | RX898                                 |
      | author      | X26                                   |
    And a DocumentReference resource exists with values:
      | property    | value                                 |
      | id          | RX898-1111111111-SearchNHSDocRefTest2 |
      | subject     | 9999999999                            |
      | status      | current                               |
      | type        | 736253002                             |
      | category    | 734163000                             |
      | contentType | application/pdf                       |
      | url         | https://example.org/my-doc.pdf        |
      | custodian   | RX898                                 |
      | author      | X26                                   |
    When producer 'RX898' searches for DocumentReferences with parameters:
      | parameter | value      |
      | subject   | 9278693472 |
    Then the response status code is 200
    And the response is a searchset Bundle
    And the Bundle has a total of 1
    And the Bundle has 1 entry
    And the Bundle contains an DocumentReference with values
      | property    | value                                 |
      | id          | RX898-1111111111-SearchNHSDocRefTest1 |
      | subject     | 9278693472                            |
      | status      | current                               |
      | type        | 736253002                             |
      | category    | 734163000                             |
      | contentType | application/pdf                       |
      | url         | https://example.org/my-doc.pdf        |
      | custodian   | RX898                                 |
      | author      | X26                                   |
    And the Bundle does not contain a DocumentReference with ID 'RX898-1111111111-SearchNHSDocRefTest2'

  Scenario: Search for DocumentReferences by pointer type and NHS number
    Given the application 'DataShare' (ID 'z00z-y11y-x22x') is registered to access the API
    And the organisation 'RX898' is authorised to access pointer types:
      | system                 | value            |
      | http://snomed.info/sct | 736253002        |
      | http://snomed.info/sct | 1363501000000100 |
    And a DocumentReference resource exists with values:
      | property    | value                                 |
      | id          | RX898-1111111111-SearchNHSDocRefTest1 |
      | subject     | 9278693472                            |
      | status      | current                               |
      | type        | 736253002                             |
      | category    | 734163000                             |
      | contentType | application/pdf                       |
      | url         | https://example.org/my-doc.pdf        |
      | custodian   | RX898                                 |
      | author      | X26                                   |
    And a DocumentReference resource exists with values:
      | property    | value                                 |
      | id          | RX898-1111111111-SearchNHSDocRefTest2 |
      | subject     | 9999999999                            |
      | status      | current                               |
      | type        | 736253002                             |
      | category    | 734163000                             |
      | contentType | application/pdf                       |
      | url         | https://example.org/my-doc.pdf        |
      | custodian   | RX898                                 |
      | author      | X26                                   |
    And a DocumentReference resource exists with values:
      | property    | value                                 |
      | id          | RX898-1111111111-SearchNHSDocRefTest3 |
      | subject     | 9999999999                            |
      | status      | current                               |
      | type        | 1363501000000100                      |
      | category    | 734163000                             |
      | contentType | application/pdf                       |
      | url         | https://example.org/my-doc.pdf        |
      | custodian   | RX898                                 |
      | author      | X26                                   |
    When producer 'RX898' searches for DocumentReferences with parameters:
      | parameter    | value      |
      | pointer_type | 736253002  |
      | subject      | 9999999999 |
    Then the response status code is 200
    And the response is a searchset Bundle
    And the Bundle has a total of 1
    And the Bundle has 1 entry
    And the Bundle contains an DocumentReference with values
      | property    | value                                 |
      | id          | RX898-1111111111-SearchNHSDocRefTest2 |
      | subject     | 9999999999                            |
      | status      | current                               |
      | type        | 736253002                             |
      | category    | 734163000                             |
      | contentType | application/pdf                       |
      | url         | https://example.org/my-doc.pdf        |
      | custodian   | RX898                                 |
      | author      | X26                                   |
    And the Bundle does not contain a DocumentReference with ID 'RX898-1111111111-SearchNHSDocRefTest1'
    And the Bundle does not contain a DocumentReference with ID 'RX898-1111111111-SearchNHSDocRefTest3'
