Feature: Consumer - countDocumentReference - Success Scenarios

  Scenario: Single pointer found for patient
    Given the application 'DataShare' (ID 'z00z-y11y-x22x') is registered to access the API
    And the organisation 'RX898' is authorised to access pointer types:
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    And a DocumentReference resource exists with values:
      | property    | value                            |
      | id          | 8FW23-1114567890-CountDocRefTest |
      | subject     | 9278693472                       |
      | status      | current                          |
      | type        | 736253002                        |
      | contentType | application/pdf                  |
      | url         | https://example.org/my-doc.pdf   |
      | custodian   | 8FW23                            |
    When consumer 'RX898' counts DocumentReferences with parameters:
      | parameter          | value                                         |
      | subject:identifier | https://fhir.nhs.uk/Id/nhs-number\|9278693472 |
    Then the response status code is 200
    And the response is a searchset Bundle
    And the Bundle has a total of 1
    And the response does not contain the key 'entry'

  Scenario: No pointers found for patient
    Given the application 'DataShare' (ID 'z00z-y11y-x22x') is registered to access the API
    And the organisation 'RX898' is authorised to access pointer types:
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    And a DocumentReference resource exists with values:
      | property    | value                            |
      | id          | 8FW23-1114567890-CountNoPointers |
      | subject     | 9999999999                       |
      | status      | current                          |
      | type        | 736253002                        |
      | contentType | application/pdf                  |
      | url         | https://example.org/my-doc.pdf   |
      | custodian   | 8FW23                            |
    When consumer 'RX898' counts DocumentReferences with parameters:
      | parameter          | value                                         |
      | subject:identifier | https://fhir.nhs.uk/Id/nhs-number\|9995001624 |
    Then the response status code is 200
    And the response is a searchset Bundle
    And the Bundle has a total of 0
    And the response does not contain the key 'entry'

  Scenario: Multiple pointers found for patient
    Given the application 'DataShare' (ID 'z00z-y11y-x22x') is registered to access the API
    And the organisation 'RX898' is authorised to access pointer types:
      | system                 | value           |
      | http://snomed.info/sct | 736253002       |
      | http://snomed.info/sct | 887701000000100 |
    And a DocumentReference resource exists with values:
      | property    | value                          |
      | id          | 8FW23-1114567890-CountMultiple |
      | subject     | 9278693472                     |
      | status      | current                        |
      | type        | 736253002                      |
      | contentType | application/pdf                |
      | url         | https://example.org/my-doc.pdf |
      | custodian   | 8FW23                          |
    And a DocumentReference resource exists with values:
      | property    | value                           |
      | id          | 8FW23-1114567890-CountMultiple2 |
      | subject     | 9278693472                      |
      | status      | current                         |
      | type        | 887701000000100                 |
      | contentType | application/pdf                 |
      | url         | https://example.org/my-doc2.pdf |
      | custodian   | 8FW23                           |
    And a DocumentReference resource exists with values:
      | property    | value                           |
      | id          | 8FW23-1114567890-CountMultiple3 |
      | subject     | 9278693472                      |
      | status      | current                         |
      | type        | 887701000000100                 |
      | contentType | application/pdf                 |
      | url         | https://example.org/my-doc3.pdf |
      | custodian   | 8FW23                           |
    When consumer 'RX898' counts DocumentReferences with parameters:
      | parameter          | value                                         |
      | subject:identifier | https://fhir.nhs.uk/Id/nhs-number\|9278693472 |
    Then the response status code is 200
    And the response is a searchset Bundle
    And the Bundle has a total of 3
    And the response does not contain the key 'entry'
