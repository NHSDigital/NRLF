Feature: Consumer - searchDocumentReference - Success Scenarios

  Scenario: Search for a DocumentReference by NHS Number
    Given the application 'DataShare' (ID 'z00z-y11y-x22x') is registered to access the API
    And the organisation 'Yorkshire Ambulance Service' (ODS Code 'RX898') is authorised to access pointer types:
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    And a DocumentReference resource exists with values:
      | property    | value                           |
      | id          | 02V-1234567890-SearchDocRefTest |
      | subject     | 9278693472                      |
      | status      | current                         |
      | type        | 736253002                       |
      | contentType | application/pdf                 |
      | url         | https://example.org/my-doc.pdf  |
      | custodian   | 02V                             |
    When the organisation 'RX898' requests to search for DocumentReferences with parameters:
      | parameter | value      |
      | subject   | 9278693472 |
    Then the response status code is 200
    And the response is a Bundle with 1 entries
    And the Bundle contains an DocumentReference entry with values
      | property    | value                           |
      | id          | 02V-1234567890-SearchDocRefTest |
      | subject     | 9278693472                      |
      | status      | current                         |
      | type        | 736253002                       |
      | contentType | application/pdf                 |
      | url         | https://example.org/my-doc.pdf  |
      | custodian   | 02V                             |

  Scenario: Search for multiple DocumentReferences by NHS number
    Given the application 'DataShare' (ID 'z00z-y11y-x22x') is registered to access the API
    And the organisation 'Yorkshire Ambulance Service' (ODS Code 'RX898') is authorised to access pointer types:
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    And a DocumentReference resource exists with values:
      | property    | value                                 |
      | id          | 02V-1234567890-SearchMultipleRefTest1 |
      | subject     | 9278693472                            |
      | status      | current                               |
      | type        | 736253002                             |
      | contentType | application/pdf                       |
      | url         | https://example.org/my-doc-1.pdf      |
      | custodian   | 02V                                   |
    And a DocumentReference resource exists with values:
      | property    | value                                 |
      | id          | 02V-1234567890-SearchMultipleRefTest2 |
      | subject     | 9278693472                            |
      | status      | current                               |
      | type        | 736253002                             |
      | contentType | application/pdf                       |
      | url         | https://example.org/my-doc-2.pdf      |
      | custodian   | 02V                                   |
    And a DocumentReference resource exists with values:
      | property    | value                                 |
      | id          | 02V-1234567890-SearchMultipleRefTest3 |
      | subject     | 9278693472                            |
      | status      | current                               |
      | type        | 887701000000100                       |
      | contentType | application/pdf                       |
      | url         | https://example.org/my-doc-3.pdf      |
      | custodian   | 02V                                   |
    When the organisation 'RX898' requests to search for DocumentReferences with parameters:
      | parameter | value      |
      | subject   | 9278693472 |
    Then the response status code is 200
    And the response is a Bundle with 2 entries
    And the Bundle contains an DocumentReference entry with values
      | property    | value                                 |
      | id          | 02V-1234567890-SearchMultipleRefTest1 |
      | subject     | 9999999999                            |
      | status      | current                               |
      | type        | 736253002                             |
      | contentType | application/pdf                       |
      | url         | https://example.org/my-doc-1.pdf      |
      | custodian   | 02V                                   |
    And the Bundle contains an DocumentReference entry with values
      | property    | value                                 |
      | id          | 02V-1111111111-SearchMultipleRefTest2 |
      | subject     | 9999999999                            |
      | status      | current                               |
      | type        | 736253002                             |
      | contentType | application/pdf                       |
      | url         | https://example.org/my-doc-2.pdf      |
      | custodian   | 02V                                   |
    And the Bundle does not contain a DocumentReference with ID '02V-1111111111-SearchMultipleRefTest3'

  Scenario: Search for multiple DocumentReferences by NHS number - S3 authorisation
    Given the application 'DataShare' (ID 'z00z-y11y-x22x') is registered to access the API
    And the application is configured to lookup permissions from S3
    And the organisation 'Yorkshire Ambulance Service' (ODS Code 'RX898') is authorised in S3 to access pointer types:
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    And a DocumentReference resource exists with values:
      | property    | value                                 |
      | id          | 02V-1234567890-SearchMultipleRefTest1 |
      | subject     | 9278693472                            |
      | status      | current                               |
      | type        | 736253002                             |
      | contentType | application/pdf                       |
      | url         | https://example.org/my-doc-1.pdf      |
      | custodian   | 02V                                   |
    And a DocumentReference resource exists with values:
      | property    | value                                 |
      | id          | 02V-1234567890-SearchMultipleRefTest2 |
      | subject     | 9278693472                            |
      | status      | current                               |
      | type        | 736253002                             |
      | contentType | application/pdf                       |
      | url         | https://example.org/my-doc-2.pdf      |
      | custodian   | 02V                                   |
    And a DocumentReference resource exists with values:
      | property    | value                                 |
      | id          | 02V-1234567890-SearchMultipleRefTest3 |
      | subject     | 9278693472                            |
      | status      | current                               |
      | type        | 887701000000100                       |
      | contentType | application/pdf                       |
      | url         | https://example.org/my-doc-3.pdf      |
      | custodian   | 02V                                   |
    When the organisation 'RX898' requests to search for DocumentReferences with parameters:
      | parameter | value      |
      | subject   | 9278693472 |
    Then the response status code is 200
    And the response is a Bundle with 2 entries
    And the Bundle contains an DocumentReference entry with values
      | property    | value                                 |
      | id          | 02V-1234567890-SearchMultipleRefTest1 |
      | subject     | 9278693472                            |
      | status      | current                               |
      | type        | 736253002                             |
      | contentType | application/pdf                       |
      | url         | https://example.org/my-doc-1.pdf      |
      | custodian   | 02V                                   |
    And the Bundle contains an DocumentReference entry with values
      | property    | value                                 |
      | id          | 02V-1111111111-SearchMultipleRefTest2 |
      | subject     | 9278693472                            |
      | status      | current                               |
      | type        | 736253002                             |
      | contentType | application/pdf                       |
      | url         | https://example.org/my-doc-2.pdf      |
      | custodian   | 02V                                   |
    And the Bundle does not contain a DocumentReference with ID '02V-1111111111-SearchMultipleRefTest3'

# No pointers found
# Pointers exist but no permissions
# Search by custodian
