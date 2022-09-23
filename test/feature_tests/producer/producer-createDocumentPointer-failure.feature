Feature: Failure Scenarios where producer unable to create a Document Pointer

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

  
    Scenario: Failed to create a Document Pointer with incorrect permissions 

        Given Producer "CUTHBERT'S CLOSE CARE HOME" does not have permissions to create Document Pointers for:
            | snomed_code   | description                       |
            | "736253002"   | "Mental health crisis plan"       |
         When Producer "CUTHBERT'S CLOSE CARE HOME" creates a Document Reference from DOCUMENT template:
            | property      | value                             |
            | identifier    | "1234567892"                      |
            | type          | "887701000000100"                 |
            | custodian     | "CUTHBERT'S CLOSE CARE HOME"      |
            | subject       | "2742179658"                      |
            | contentType   | "application/pdf"                 |
            | url           | "https://example.org/my-doc.pdf"  |
         Then the operation is unsuccessful
          And the response contains error message "Required permissions to create a document pointer are missing"
    

    Scenario: Failed to create a Document Pointer with a non existent producer

        Given Producer "CUTHBERT'S CLOSE CARE HOME4" does not exist in the system
         When Producer "CUTHBERT'S CLOSE CARE HOME4" creates a Document Reference from DOCUMENT template:
            | property      | value                             |
            | identifier    | "1234567892"                      |
            | type          | "887701000000100"                 |
            | custodian     | "CUTHBERT'S CLOSE CARE HOME4"     |
            | subject       | "2742179658"                      |
            | contentType   | "application/pdf"                 |
            | url           | "https://example.org/my-doc.pdf"  |
         Then the operation is unsuccessful
          And the response contains error message "Custodian does not exist in the system"

    
    Scenario Outline: Failed to create a Document Pointer due to missing/invalid required params

        Given Producer "AARON COURT MENTAL NH" has permissions to create Document Pointers for:
            | snomed_code   | description                       |
            | "736253002"   | "Mental health crisis plan"       |
         When Producer "AARON COURT MENTAL NH" creates a Document Reference from DOCUMENT template:
            | Identifier    | <identifier>                      |
            | type          | <type>                            |
            | custodian     | "AARON COURT MENTAL NH"           |
            | subject       | <subject>                         |
            | url           | <url>                             |
         Then the operation is unsuccessful
          And the response contains error message <error_message>                           

        Examples:
            | identifier   | type        | subject      |  url                              | error_message                                                     |  
            | "1234567890" | "736253002" | "45646"      | "https://example.org/my-doc.pdf"  | "The NHS number does not conform to the NHS Number format: 45646" |
            | "1234567890" | "736253002" | "9278693472" | "https://example.org"             | "Resource is invalid : url"                                       |
            | "1234567890" | "67"        | "9278693472" | "https://example.org/my-doc.pdf"  | "Code '67' from system 'http://snomed.info/sct' does not exist"   |


    Scenario: Failed to create a Document Pointer as document already exists in the system

        Given a Document Pointer exists in the system with the below values
            | property      | value                             |
            | identifier    | "1234567890"                      |
            | type          | "736253002"                       |
            | custodian     | "AARON COURT MENTAL NH"           |
            | subject       | "9278693472"                      |
            | contentType   | "application/pdf"                 |
            | url           | "https://example.org/my-doc.pdf"  |
         And Producer "AARON COURT MENTAL NH" has permissions to create Document Pointers for:
            | snomed_code   | description                       |
            | "736253002"   | "Mental health crisis plan"       |
         When Producer "AARON COURT MENTAL NH" creates a Document Reference from DOCUMENT template:
            | property      | value                             |
            | identifier    | "1234567890"                      |
            | type          | "736253002"                       |
            | custodian     | "AARON COURT MENTAL NH"           |
            | subject       | "9278693472"                      |
            | contentType   | "application/pdf"                 |
            | url           | "https://example.org/my-doc.pdf"  |
         Then the operation is unsuccessful
          And the response contains error message "Duplicate rejected"  
    
    
    Scenario: Failed to create a Document Pointer due to internal server error

        Given Producer "AARON COURT MENTAL NH" has permissions to create Document Pointers for:
            | snomed_code   | description                       |
            | "736253002"   | "Mental health crisis plan"       |
         When Producer "AARON COURT MENTAL NH" creates a Document Reference from DOCUMENT template:
            | property      | value                             |
            | identifier    | "1234567890"                      |
            | type          | "736253002"                       |
            | custodian     | "AARON COURT MENTAL NH"           |
            | subject       | "9278693472"                      |
            | contentType   | "application/pdf"                 |
            | url           | "https://example.org/my-doc.pdf"  |
         Then the operation is unsuccessful
          And the response contains error message "Internal server error"
