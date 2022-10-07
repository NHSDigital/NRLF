Feature: Failure Scenarios - Superseded a Document pointer

    Background:
        Given the following DOCUMENT_POINTER exists:
            | property         | value                                 |
            | identifier       | "1234567890"                          |
            | status           | "current"                             |
            | type             | "736253002"                           |
            | custodian        | "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL"|
            | subject          | "Patient/9278693472"                  |
            | contentType      | "application/pdf"                     |
            | url              | "https://example.org/my-doc.pdf"      |

          And the following DOCUMENT_POINTER exists:
            | property         | value                                 |
            | identifier       | "1234567895"                          |
            | status           | "entered-in-error"                    |
            | type             | "736253002"                           |
            | custodian        | "AARON COURT MENTAL NH"               |
            | subject          | "Patient/7959557624"                  |
            | contentType      | "application/pdf"                     |
            | url              | "https://example.org/my-doc5.pdf"     |

          And template SUPERSEDE_DOCUMENT
            """
            {
                "masterIdentifier": "$custodian|$identifier",
                  "custodian": {
                    "system": "https://fhir.nhs.uk/Id/accredited-system-id",
                    "id": "$custodian"
                },
                "subject": {
                    "system": "https://fhir.nhs.uk/Id/nhs-number",
                    "id": "$subject"
                },
                 "type": {
                    "coding": [{
                        "system": "https://snomed.info/ict",
                        "code": "$type"
                    }]
                },
                 "relatesTo": [{
                    "code": "$code",
                    "target": {
                        "type": "DocumentReference",
                        "identifier": "$target"
                    }
                }],
                  "content": [{
                    "attachment": {
                        "contentType: $contentType,
                        "url": "$url"
                    }
                }]
            }
            """

    Scenario: Producer does not exist

        Given Producer "ACUTE MENTALHEALTH UNIT" does not exist in the system
        When Producer "ACUTE MENTALHEALTH UNIT" supersedes a Document Pointer from SUPERSEDE_DOCUMENT template:
            | property      | value                                 |
            | identifier    | "0987654321"                          |
            | target        | "DocumentReference/1234567890"        |
            | relation      | "appends"                             |
            | type          | "736253002"                           |
            | custodian     | "ACUTE MENTALHEALTH UNIT"             |
            | subject       | "Patient/9278693472"                  |
            | contentType   | "application/pdf"                     |
            | url           | "https://example.org/my-doc2.pdf"     |
        Then the operation is unsuccessful
            And the response contains error message "Custodian does not exist in the system"

    Scenario: Producer does not have permission

        Given Producer "AARON COURT MENTAL NH" does not have permission to supersede Document Pointers for:
            | snomed_code   | description                           |
            | "736253002"   | "Mental health crisis plan"           |
        When Producer "AARON COURT MENTAL NH" supersedes a Document Pointer from SUPERSEDE_DOCUMENT template:
            | property      | value                                 |
            | identifier    | "0987654321"                          |
            | target        | "DocumentReference/1234567890"        |
            | relation      | "appends"                             |
            | type          | "736253002"                           |
            | custodian     | "AARON COURT MENTAL NH"               |
            | subject       | "Patient/9278693472"                  |
            | contentType   | "application/pdf"                     |
            | url           | "https://example.org/my-doc2.pdf"     |
        Then the operation is unsuccessful
            And the response contains error message "Required permission to supersede a document pointer are missing"

    Scenario: Target document does not exist

        Given Producer "ACUTE MENTALHEALTH UNIT" has permission to supersede Document Pointers for:
            | snomed_code   | description                           |
            | "736253002"   | "Mental health crisis plan"           |
        When Producer "ACUTE MENTALHEALTH UNIT" supersedes a Document Pointer from SUPERSEDE_DOCUMENT template:
            | property      | value                                 |
            | identifier    | "0987654321"                          |
            | target        | "DocumentReference/000000000"         |
            | relation      | "appends"                             |
            | type          | "736253002"                           |
            | custodian     | "ACUTE MENTALHEALTH UNIT"             |
            | subject       | "Patient/9278693472"                  |
            | contentType   | "application/pdf"                     |
            | url           | "https://example.org/my-doc2.pdf"     |
        Then the operation is unsuccessful
            And the response contains error message "Document does not exist in the system"


    Scenario: Invalid target reference value

        Given Producer "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL" has permission to create Document Pointers for:
            | snomed_code   | description                           |
            | "736253002"   | "Mental health crisis plan"           |
        When Producer "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL" supersedes a Document Pointer from SUPERSEDE_DOCUMENT template:
            | property      | value                                 |
            | identifier    | "0987654321"                          |
            | target        | "DocumentReference/1234567890"        |
            | relation      | "replaced"                            |
            | type          | "736253002"                           |
            | custodian     | "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL"|
            | subject       | "Patient/9278693472"                  |
            | contentType   | "application/pdf"                     |
            | url           | "https://example.org/my-doc2.pdf"     |
        Then the operation is unsuccessful
            And the response contains error message "Value is not exactly equal to fixed value 'replaces'"

    Scenario Outline: Missing/invalid required params

        Given Producer "AARON COURT MENTAL NH" has permission to supersede Document Pointers for:
            | snomed_code   | description                       |
            | "736253002"   | "Mental health crisis plan"       |
        When Producer "AARON COURT MENTAL NH" supersedes a Document Reference from SUPERSEDE_DOCUMENT template:
            | Identifier    | <identifier>                      |
            | type          | <type>                            |
            | custodian     | "AARON COURT MENTAL NH"           |
            | target        | "DocumentReference/1234567890"    |
            | subject       | <subject>                         |
            | url           | <url>                             |
        Then the operation is unsuccessful
          And the response contains error message <error_message>

          Examples:
            | identifier   | type        | subject             | url                               | error_message                                                     |
            | "1234567890" | "736253002" | "45646"             | "https://example.org/my-doc.pdf"  | "The NHS number does not conform to the NHS Number format: 45646" |
            | "1234567890" | "736253002" | " "                 | "https://example.org/my-doc.pdf"  | "The NHS number does not conform to the NHS Number format: "      |
            | "1234567890" | "736253002" | "Device/9278693472" | "https://example.org/my-doc.pdf"  | "Resource is invalid : subject"                                   |
            | "1234567890" | "736253002" | "Patient/9278693472"| "https://example.org"             | "Resource is invalid : url"                                       |
            | "1234567890" | "67"        | "Patient/9278693472"| "https://example.org/my-doc.pdf"  | "Code '67' from system 'http://snomed.info/sct' does not exist"   |


    Scenario: Document Pointer status is not current

        Given Producer "AARON COURT MENTAL NH" has permission to supersede Document Pointers for:
            | snomed_code   | description                           |
            | "736253002"   | "Mental health crisis plan"           |
        When Producer "AARON COURT MENTAL NH" supersedes a Document Pointer from SUPERSEDE_DOCUMENT template:
            | property      | value                                 |
            | identifier    | "0987654321"                          |
            | target        | "DocumentReference/1234567895"        |
            | relation      | "appends"                             |
            | type          | "736253002"                           |
            | custodian     | "AARON COURT MENTAL NH"               |
            | subject       | "Patient/7959557624"                  |
            | contentType   | "application/pdf"                     |
            | url           | "https://example.org/my-doc3.pdf"     |
        Then the operation is unsuccessful
            And the response contains error message "Document Pointer status is not current"
