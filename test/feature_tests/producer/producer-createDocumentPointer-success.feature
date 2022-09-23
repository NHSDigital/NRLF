Feature: Basic Success Scenarios where producer is able to create a Document Pointer

    Background:
        Given template DOCUMENT

            """"
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
                "content": [{
                    "attachment": {
                        "contentType: $contentType,
                        "url": "$url"
                    }
                }]
            }"""

    Scenario: Successfully create a Document Pointer of type Mental health crisis plan

        Given Producer "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL" has permission to create Document Pointers for:
            | snomed_code   | description                               |
            | "736253002"   | "Mental health crisis plan"               |
         When Producer "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL" creates a Document Pointer from DOCUMENT template:
            | property      | value                                     |
            | identifier    | "1234567890"                              |
            | type          | "736253002"                               |
            | custodian     | "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL" |
            | subject       | "9278693472"                              |
            | contentType   | "application/pdf"                         |
            | url           | "https://example.org/my-doc.pdf"          |
         Then the operation is successful
          And Document Pointer "1234567890" exists:
            | property      | value                                     |
            | status        | "current"                                 |

    
    Scenario: Successfully create a Document Pointer of type End of life care coordination summary

        Given Document Types:
            | snomed_code       | description                             |
            | "861421000000109" | "End of life care coordination summary" |
          And Producer "ABUNDANT LIFE CARE LIMITED" has permission to create Document Pointers for:
            | snomed_code       |
            | "861421000000109" |
         When Producer "ABUNDANT LIFE CARE LIMITED" creates a Document Pointer from DOCUMENT template:
            | property          | value                                   |
            | identifier        | "1234567891"                            |
            | type              | "861421000000109"                       |
            | custodian         | "ABUNDANT LIFE CARE LIMITED"            |
            | subject           | "2742179658"                            |
            | contentType       | "application/pdf"                       |
            | url               | "https://example.org/my-doc.pdf"        |
         Then the operation is successful
          And Document Pointer "1234567891" exists:
            | property          | value                                   |
            | status            | "current"                               |
            