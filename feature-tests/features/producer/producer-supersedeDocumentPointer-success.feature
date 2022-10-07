Feature: Success Scenarios

    Background:
          Given the following DOCUMENT_POINTER exists:
            | property         | value                                 |
            | identifier       | "1234567890"                          |
            | type             | "736253002"                           |
            | custodian        | "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL"|
            | subject          | "Patient/9278693472"                  |
            | contentType      | "application/pdf"                     |
            | url              | "https://example.org/my-doc.pdf"      |

          And the following DOCUMENT_POINTER exists:
            | property         | value                                 |
            | identifier       | "1234567891"                          |
            | type             | "736253002"                           |
            | custodian        | "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL"|
            | subject          | "Patient/9278693472"                  |
            | contentType      | "application/pdf"                     |
            | url              | "https://example.org/my-doc.pdf"      |

          And the following DOCUMENT_POINTER exists:
            | property         | value                                 |
            | identifier       | "1234567892"                          |
            | type             | "736253002"                           |
            | custodian        | "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL"|
            | subject          | "Patient/9278693472"                  |
            | contentType      | "application/pdf"                     |
            | url              | "https://example.org/my-doc.pdf"      |

          And the following DOCUMENT_POINTER exists:
            | property         | value                                 |
            | identifier       | "1234567893"                          |
            | type             | "736253002"                           |
            | custodian        | "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL"|
            | subject          | "Patient/9278693472"                  |
            | contentType      | "application/pdf"                     |
            | url              | "https://example.org/my-doc.pdf"      |

          And template for SUPERSEDE_DOCUMENT
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

    Scenario: Supersede a Document Pointer

        Given Producer "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL" has permission to supersede Document Pointers for:
            | snomed_code   | description                           |
            | "736253002"   | "Mental health crisis plan"           |
        When Producer "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL" supersedes a Document Pointer from SUPERSEDE_DOCUMENT template:
            | property      | value                                 |
            | identifier    | "0987654321"                          |
            | target        | "DocumentReference/1234567890"        |
            | code          | "replaces"                            |
            | type          | "736253002"                           |
            | custodian     | "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL"|
            | subject       | "9278693472"                          |
            | contentType   | "application/pdf"                     |
            | url           | "https://example.org/my-doc2.pdf"     |
        Then the operation is successful
          And following Document Pointer exists for Producer "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL" as:
            | identifier   | status       |
            | "0987654321" | "current"    |
            | "1234567890" | "superseded" |


    Scenario: Supersede multiple Document Pointers

        Given Producer "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL" has permission to supersede Document Pointers for:
            | snomed_code   | description                           |
            | "736253002"   | "Mental health crisis plan"           |
        When Producer "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL" supersedes a Document Pointer from SUPERSEDE_DOCUMENT template:
            | property      | value                                 |
            | identifier    | "0987654322"                          |
            | target        | "DocumentReference/1234567891"        |
            | target        | "DocumentReference/1234567892"        |
            | target        | "DocumentReference/1234567893"        |
            | code          | "transforms"                          |
            | type          | "736253002"                           |
            | custodian     | "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL"|
            | subject       | "Patient/9278693472"                  |
            | contentType   | "application/pdf"                     |
            | url           | "https://example.org/my-doc2.pdf"     |
        Then the operation is successful
          And following Document Pointer exists for Producer "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL" as:
            | identifier   | status       |
            | "0987654321" | "current"    |
            | "1234567891" | "superseded" |
            | "1234567892" | "superseded" |
            | "1234567893" | "superseded" |
