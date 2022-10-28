Feature: Basic Success Scenarios where producer able to read a Document Pointer
    Scenario: Successfully read a Document Pointer

        Given the following DOCUMENT_POINTER exists
            | property         | value                                     |
            | identifier       | "1234567890"                              |
            | type             | "736253002"                               |
            | custodian        | "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL" |
            | subject          | "Patient/9278693472"                      |
            | contentType      | "application/pdf"                         |
            | url              | "https://example.org/my-doc.pdf"          |

        When Producer "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL" requests a document
        And they provide the following document id "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL|1234567890"
        Then the operation is successful
            And the document is returned
