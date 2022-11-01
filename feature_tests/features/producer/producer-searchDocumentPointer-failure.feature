Feature: Basic Failure Scenarios where producer is not able to search for Document Pointers

    Scenario: Failure to search for a Document Pointer when the producer has no documents
        Given the following DOCUMENT_POINTER exists
            | property         | value                                    |
            | identifier       | "1234567890"                             |
            | type             | "736253002"                              |
            | custodian        | "EMERGENCY FOOT SERVICES"                |
            | subject          | "Patient/9278693472"                     |
            | contentType      | "application/pdf"                        |
            | url              | "https://example.org/my-doc.pdf"         |

          And the following DOCUMENT_POINTER exists
            | property         | value                                    |
            | identifier       | "1234567891"                             |
            | type             | "736253002"                              |
            | custodian        | "EMERGENCY AMBULANCE SERVICES"           |
            | subject          | "Patient/9278693472"                     |
            | contentType      | "application/pdf"                        |
            | url              | "https://example.org/my-doc-2.pdf"       |
        When Producer "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL" searches for documents related to patient "9278693472"
        Then the operation is unsuccessful

    Scenario: Failure to search for a Document Pointer when NHS number has no documents with requesting producer
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
            | custodian        | "EMERGENCY AMBULANCE SERVICES"            |
            | subject          | "Patient/7736959498"                      |
            | contentType      | "application/pdf"                         |
            | url              | "https://example.org/my-doc-2.pdf"        |
        When Producer "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL" searches for documents related to patient "7736959498"
        Then the operation is unsuccessful

    Scenario: Failure to search for a Document Pointer when provided document type does not exist
        Given the following DOCUMENT_POINTER exists
            | property         | value                                     |
            | identifier       | "1234567890"                              |
            | type             | "736253002"                               |
            | custodian        | "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL" |
            | subject          | "Patient/7736959498"                      |
            | contentType      | "application/pdf"                         |
            | url              | "https://example.org/my-doc.pdf"          |

          And the following DOCUMENT_POINTER exists
            | property         | value                                     |
            | identifier       | "1234567891"                              |
            | type             | "736253002"                               |
            | custodian        | "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL" |
            | subject          | "Patient/7736959498"                      |
            | contentType      | "application/pdf"                         |
            | url              | "https://example.org/my-doc-2.pdf"        |
        When Producer "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL" searches for documents related to patient "7736959498"
        And they provide the document type "555253002"
        Then the operation is unsuccessful
