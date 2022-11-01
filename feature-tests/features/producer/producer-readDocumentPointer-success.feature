Feature: Success scenarios where producer is able to delete a Document Pointer

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

          And the following superceded DOCUMENT_POINTER exists:
            | property                  | value                                                |
            | identifier                | "1234567894"                                         |
            | status                    | "superceded"                                         |
            | type                      | "736253002"                                          |
            | custodian                 | "AARON COURT MENTAL NH"                              |
            | subject                   | "Patient/9278693472"                                 |
            | contentType               | "application/pdf"                                    |
            | location                  | "https://example.org/my-docSuperceded.pdf"           |
            | deleted_on                | ""                                                   |

    Scenario: Delete an existing current Document Pointer

        Given Producer "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL" has permission to delete Document Pointers for:
            | snomed_code   | description                      |
            | "736253002"   | "Mental health crisis plan"      |
        When "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL" deletes an existing current DOCUMENT_POINTER "1234567890"
        Then the operation is successful
          And the response contains success message "Resource removed"
          And the deleted Document Reference "1234567890" exist in the system as:
            | deleted_on    | "2022-09-28T12:30:00+01:00"      |
            | status        | "current"                        |

    Scenario: Delete an existing current Document Pointer that was entered in error

        Given Producer "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL" has permission to delete Document Pointers for:
            | snomed_code   | description                      |
            | "736253002"   | "Mental health crisis plan"      |
        When "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL" deletes an existing current DOCUMENT_POINTER "1234567890" with the following attribute:
            | status        | "entered-in-error"               |
        Then the operation is successful
          And the response contains success message "Resource removed"
          And the deleted Document Reference "1234567890" exist in the system as:
            | deleted_on    | "2022-09-28T12:30:00+01:00"      |
            | status        | "entered-in-error"               |

    Scenario: Delete an existing superceded Document Pointer

        Given Producer "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL" has permission to delete Document Pointers for:
            | snomed_code   | description                       |
            | "736253002"   | "Mental health crisis plan"       |
          And DOCUMENT POINTER "1234567894" exist in the system as status 'superceded'
        When Producer "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL" deletes the DOCUMENT POINTER "1234567894"
        Then the operation is successful
          And the response contains success message "Resource removed"
          And the deleted Document Reference "1234567894" exist in the system as:
            | deleted_on    | "2022-09-28T12:30:00+01:00"   |
            | status        | "entered-in-error"            |
