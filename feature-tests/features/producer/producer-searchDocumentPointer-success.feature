Feature: Basic Success Scenarios where producer is able to search for Document Pointers
    Scenario: Successfully search for multiple Document Pointers by NHS number

        Given the following DOCUMENT_POINTER exists
            | property         | value                                     |
            | identifier       | "1234567890"                              |
            | type             | "736253002"                               |
            | custodian        | "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL" |
            | subject          | "Patient/9278693472"                      |
            | contentType      | "application/pdf"                         |
            | url              | "https://example.org/my-doc.pdf"          |

          And the following DOCUMENT_POINTER exists
            | property         | value                                     |
            | identifier       | "1234567891"                              |
            | type             | "736253002"                               |
            | custodian        | "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL" |
            | subject          | "Patient/9278693472"                      |
            | contentType      | "application/pdf"                         |
            | url              | "https://example.org/my-doc-2.pdf"        |
        When Producer "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL" searches for documents related to patient "9278693472"
        Then the operation is successful
            And the following documents are returned

    Scenario: Successfully search for multiple Document Pointers by NHS number with provided document type

        Given the following DOCUMENT_POINTER exists
            | property         | value                                     |
            | identifier       | "1234567890"                              |
            | type             | "736253002"                               |
            | custodian        | "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL" |
            | subject          | "Patient/9278693472"                      |
            | contentType      | "application/pdf"                         |
            | url              | "https://example.org/my-doc.pdf"          |

          And the following DOCUMENT_POINTER exists
            | property         | value                                     |
            | identifier       | "1234567891"                              |
            | type             | "736253002"                               |
            | custodian        | "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL" |
            | subject          | "Patient/9278693472"                      |
            | contentType      | "application/pdf"                         |
            | url              | "https://example.org/my-doc-2.pdf"        |
        When Producer "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL" searches for documents related to patient "9278693472"
        And they provide the document type "736253002"
        Then the operation is successful
            And the following documents are returned

    Scenario: Successful search returns a single Document Pointer by NHS number

        Given the following DOCUMENT_POINTER exists
            | property         | value                                    |
            | identifier       | "1234567890"                             |
            | type             | "736253002"                              |
            | custodian        | "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL"|
            | subject          | "Patient/9278693472"                     |
            | contentType      | "application/pdf"                        |
            | url              | "https://example.org/my-doc.pdf"         |

          And the following DOCUMENT_POINTER exists
            | property         | value                                    |
            | identifier       | "1234567891"                             |
            | type             | "736253002"                              |
            | custodian        | "A DIFFERENT CUSTODIAN FOR AMBULANCES"|
            | subject          | "Patient/9278693472"                     |
            | contentType      | "application/pdf"                        |
            | url              | "https://example.org/my-doc-2.pdf"         |
        When Producer "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL" searches for documents related to patient "9278693472"
        Then the operation is successful
            And the following documents are returned
            And it does not contain "document 2"
