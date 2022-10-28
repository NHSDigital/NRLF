Feature: Basic Failure Scenarios where producer is not able to read a Document Pointer
    Scenario: Fail to read a Document Pointer when it does not exist
        Given the following DOCUMENT_POINTER exists
            | property         | value                                     |
            | identifier       | "1234567890"                              |
            | type             | "736253002"                               |
            | custodian        | "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL" |
            | subject          | "Patient/9278693472"                      |
            | contentType      | "application/pdf"                         |
            | url              | "https://example.org/my-doc.pdf"          |

        When Producer "NATIONAL AMBULANCE SERVICE" requests a document
        And they provide the following document id "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL|1234567890"
        Then the operation is unsuccessful

    Scenario: Fail to read a Document Pointer when producer does not own the document
        Given the following DOCUMENT_POINTER exists
            | property         | value                                     |
            | identifier       | "1234567890"                              |
            | type             | "736253002"                               |
            | custodian        | "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL" |
            | subject          | "Patient/9278693472"                      |
            | contentType      | "application/pdf"                         |
            | url              | "https://example.org/my-doc.pdf"          |

        When Producer "NATIONAL AMBULANCE SERVICE" requests a document
        And they provide the following document id "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL|1234567890"
        Then the operation is unsuccessful
        And the response contains error message "Permission Denied"
