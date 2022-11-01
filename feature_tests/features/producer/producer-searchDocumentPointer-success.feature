@local
Feature: Basic Success Scenarios where producer is able to search for Document Pointers

  Background:
    Given template DOCUMENT
      """
      {
        "resourceType": "DocumentReference",
        "masterIdentifier": {
          "value": "$custodian|$identifier"
        },
        "custodian": {
          "system": "https://fhir.nhs.uk/Id/accredited-system-id",
          "id": "$custodian"
        },
        "subject": {
          "system": "https://fhir.nhs.uk/Id/nhs-number",
          "id": "$subject"
        },
        "type": {
          "coding": [
            {
              "system": "https://snomed.info/ict",
              "code": "$type"
            }
          ]
        },
        "content": [
          {
            "attachment": {
              "contentType": "$contentType",
              "url": "$url"
            }
          }
        ],
        "status": "current"
      }
      """

  Scenario: Successfully search for multiple Document Pointers by NHS number
    Given a Document Pointer exists in the system with the below values
      | property    | value                             |
      | identifier  | 1114567890                        |
      | type        | 736253002                         |
      | custodian   | AARON COURT MENTAL NH             |
      | subject     | 9278693472                        |
      | contentType | application/pdf                   |
      | url         | https://example.org/my-doc.pdf    |
    And a Document Pointer exists in the system with the below values
      | property    | value                             |
      | identifier  | 2224567890                        |
      | type        | 736253002                         |
      | custodian   | AARON COURT MENTAL NH             |
      | subject     | 9278693472                        |
      | contentType | application/pdf                   |
      | url         | https://example.org/my-doc-2.pdf  |
    And Producer "AARON COURT MENTAL NH" has permission to search Document Pointers for
      | snomed_code | description                       |
      | 736253002   | Mental health crisis plan         |
    When "AARON COURT MENTAL NH" searches with query parameters:
      | property      | value                           |
      | subject       | 9278693472                      |
    And "AARON COURT MENTAL NH" searches with the header values:
      | property      | value                           |
      | type          | 736253002                       |
      | custodian     | AARON COURT MENTAL NH           |
    Then the search is made
    And the operation is successful
    And 2 document references were returned
    And the response contains the DOCUMENT template with the below values
      | property    | value                             |
      | identifier  | 1114567890                        |
      | type        | 736253002                         |
      | custodian   | AARON COURT MENTAL NH             |
      | subject     | 9278693472                        |
      | contentType | application/pdf                   |
      | url         | https://example.org/my-doc.pdf    |
    And the response contains the DOCUMENT template with the below values
      | property    | value                             |
      | identifier  | 2224567890                        |
      | type        | 736253002                         |
      | custodian   | AARON COURT MENTAL NH             |
      | subject     | 9278693472                        |
      | contentType | application/pdf                   |
      | url         | https://example.org/my-doc-2.pdf  |






    # Scenario: Successfully search for multiple Document Pointers by NHS number with provided document type

    #     Given the following DOCUMENT_POINTER exists
    #         | property         | value                                     |
    #         | identifier       | "1234567890"                              |
    #         | type             | "736253002"                               |
    #         | custodian        | "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL" |
    #         | subject          | "Patient/9278693472"                      |
    #         | contentType      | "application/pdf"                         |
    #         | url              | "https://example.org/my-doc.pdf"          |

    #       And the following DOCUMENT_POINTER exists
    #         | property         | value                                     |
    #         | identifier       | "1234567891"                              |
    #         | type             | "736253002"                               |
    #         | custodian        | "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL" |
    #         | subject          | "Patient/9278693472"                      |
    #         | contentType      | "application/pdf"                         |
    #         | url              | "https://example.org/my-doc-2.pdf"        |
    #     When Producer "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL" searches for documents related to patient "9278693472"
    #     And they provide the document type "736253002"
    #     Then the operation is successful
    #         And the following documents are returned

    # Scenario: Successful search returns a single Document Pointer by NHS number

    #     Given the following DOCUMENT_POINTER exists
    #         | property         | value                                    |
    #         | identifier       | "1234567890"                             |
    #         | type             | "736253002"                              |
    #         | custodian        | "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL"|
    #         | subject          | "Patient/9278693472"                     |
    #         | contentType      | "application/pdf"                        |
    #         | url              | "https://example.org/my-doc.pdf"         |

    #       And the following DOCUMENT_POINTER exists
    #         | property         | value                                    |
    #         | identifier       | "1234567891"                             |
    #         | type             | "736253002"                              |
    #         | custodian        | "A DIFFERENT CUSTODIAN FOR AMBULANCES"|
    #         | subject          | "Patient/9278693472"                     |
    #         | contentType      | "application/pdf"                        |
    #         | url              | "https://example.org/my-doc-2.pdf"         |
    #     When Producer "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL" searches for documents related to patient "9278693472"
    #     Then the operation is successful
    #         And the following documents are returned
    #         And it does not contain "document 2"
