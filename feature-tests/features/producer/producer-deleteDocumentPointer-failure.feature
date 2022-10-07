Feature: Failure scenarios where producer is unable to delete a Document Pointer

     Background:
        Given the following current DOCUMENT_POINTER exists:
            | propertyname              | value                                                |
            | identifier                | "1234567890"                                         |
            | status                    | "current"                                            |
            | type                      | "736253002"                                          |
            | subject                   | "Patient/9278693472"                                 |
            | date                      | "2022-09-27T12:30:00+01:00"                          |
            | custodian                 | "Organization/f001"                                  |
            | location                  | "https://example.org/my-doc.pdf"                     |
            | contenttype               | "application/pdf"                                    |
            | deleted_on                | ""                                                   |

        And the following deleted DOCUMENT_POINTER exists:
            | property                  | value                                                |
            | identifier                | "1234567895"                                         |
            | status                    | "entered-in-error"                                   |
            | type                      | "736253002"                                          |
            | custodian                 | "AARON COURT MENTAL NH"                              |
            | subject                   | "Patient/9278693472"                                 |
            | contentType               | "application/pdf"                                    |
            | location                  | "https://example.org/my-docDeleted.pdf"              |
            | deleted_on                | ""                                                   |

    Scenario: Unable to delete a Document Pointer when the Producer does not have permission

        Given Producer "CUTHBERT'S CLOSE CARE HOME" does not have permission to delete the Document Pointers for:
            | snomed_code   | description                                |
            | "736253002"   | "Mental health crisis plan"                |
        When Producer "CUTHBERT'S CLOSE CARE HOME" deletes an existing current DOCUMENT_POINTER "1234567890"
        Then the operation is unsuccessful
          And the response contains error message "Required permissions to delete a DocumentReference are missing"

    Scenario: Unable to delete a Document Pointer when the Producer does not exist

        Given Producer "Lancashire Care" does not exist in the system
         When Producer "Lancashire Care" deletes an existing current DOCUMENT_POINTER "1234567890"
         Then the operation is unsuccessful
          And the response contains error message "Custodian does not exist in the system"

    Scenario: Unable to delete a Document Pointer that does not exist

        Given Producer "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL" has permission to delete Document Pointers for:
            | snomed_code   | description                               |
            | "736253002"   | "Mental health crisis plan"               |
          And DOCUMENT_POINTER "7852369851" does not exist in the system
        When Producer "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL" deletes the DOCUMENT_POINTER "7852369851"
        Then the operation is unsuccessful
          And the response contains error message "DocumentReference does not exist in the system"

    Scenario: Unable to delete a Document Pointer that was already deleted

        Given Producer "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL" has permission to delete Document Pointers for:
            | snomed_code   | description                               |
            | "736253002"   | "Mental health crisis plan"               |
          And DOCUMENT POINTER "1234567895" exist in the system as status 'entered-in-error'
        When Producer "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL" deletes the DOCUMENT_POINTER "1234567895"
        Then the operation is unsuccessful
          And the response contains error message "DocumentReference does not exist in the system"
