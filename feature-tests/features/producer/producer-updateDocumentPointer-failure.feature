# Feature: Failure scenarios where producer is unable to update a Document Pointer
# Background:
# Given the following current DOCUMENT_POINTER exists:
# | property                  | value                                                |
# | masterIdentifier          | "f001|1234567890"                                    |
# | identifier                | "1234567890"                                         |
# | status                    | "current"                                            |
# | docStatus                 | "preliminary"                                        |
# | type                      | "736253002"                                          |
# | category                  | "Medication Summary Document"                        |
# | subject                   | "Patient/9278693472"                                 |
# | date                      | "2022-09-27T12:30:00+01:00"                          |
# | author                    | "Practitioner/xcda1"                                 |
# | authenticator             | "Organization/f001"                                  |
# | custodian                 | "Organization/f001"                                  |
# | relation                  | "appends"                                            |
# | relatesto                 | "DocumentReference/7536941082"                       |
# | description               | "Medication Summary Document for Patient 9278693472" |
# | securityLabel             | "restricted"                                         |
# | location                  | "https://example.org/my-doc.pdf"                     |
# | language                  | "en-GB"                                              |
# | contenttype               | "application/pdf"                                    |
# | format                    | "urn:nhs:PDF"                                        |
# | encounter                 | "Encounter/HH"                                       |
# | event                     | "mental health program"                              |
# | period                    | "2022-09-27T12:30:00+01:00"                          |
# | facility                  | "Hospital outpatient mental health center"           |
# | setting                   | "Adult mental illness"                               |
# | patientInfo               | "9278693472"                                         |
# | related                   | "7536941082"                                         |
# And the following superceded DOCUMENT_POINTER exists:
# | property                  | value                                                |
# | identifier                | "1234567894"                                         |
# | status                    | "superceded"                                         |
# | type                      | "736253002"                                          |
# | custodian                 | "AARON COURT MENTAL NH"                              |
# | subject                   | "Patient/9278693472"                                 |
# | contentType               | "application/pdf"                                    |
# | location                  | "https://example.org/my-docSuperceded.pdf"           |
# And the following deleted DOCUMENT_POINTER exists:
# | property                  | value                                                |
# | identifier                | "1234567895"                                         |
# | status                    | "entered-in-error"                                   |
# | type                      | "736253002"                                          |
# | custodian                 | "AARON COURT MENTAL NH"                              |
# | subject                   | "Patient/9278693472"                                 |
# | contentType               | "application/pdf"                                    |
# | location                  | "https://example.org/my-docDeleted.pdf"              |
# And template for UPDATE_DOCUMENT:
# ```
# {
# "resourceType":"DocumentReference",
# "masterIdentifier":"$custodian|$identifier",
# "identifier":"$identifier",
# "status":"$status",
# "docStatus":"$docStatus",
# "type":{
# "coding":[
# {
# "system":"http://snomed.info/sct",
# "code":"$type"
# }
# ],
# "category":[
# {
# "coding":[
# {
# "system":"http://ihe.net/xds/connectathon/classCodes",
# "code":"$category"
# }
# ]
# }
# ],
# "subject":{
# "system":"https://fhir.nhs.uk/Id/nhs-number",
# "id":"$subject"
# },
# "date":"$date",
# "author":{
# "reference":"$author"
# },
# "authenticator":{
# "reference":"$authenticator"
# },
# "custodian":{
# "system":"https://fhir.nhs.uk/Id/accredited-system-id",
# "id":"$custodian"
# },
# "relatesTo":[
# {
# "code":"$relation",
# "target":{
# "reference":"$relatesTo"
# }
# }
# ],
# "description":"$description",
# "securityLabel":[
# {
# "coding":[
# {
# "system":"http://terminology.hl7.org/CodeSystem/v3-Confidentiality",
# "code":"$securityLabel"
# }
# ]
# }
# ],
# "content":[
# {
# "attachment":{
# "contentType":"$contentType",
# "language":"$language",
# "url":"$location"
# },
# "format":{
# "system":"urn:oid:1.3.6.1.4.1.19376.1.2.3",
# "code":"$format"
# }
# }
# ],
# "context":{
# "encounter":[
# {
# "reference":"$encounter"
# }
# ],
# "event":[
# {
# "coding":[
# {
# "system":"http://ihe.net/xds/connectathon/eventCodes",
# "code":"$event"
# }
# ]
# }
# ],
# "period":"$date",
# "facilityType":{
# "coding":[
# {
# "system":"http://www.ihe.net/xds/connectathon/healthcareFacilityTypeCodes",
# "code":"$facility"
# }
# ]
# },
# "practiceSetting":{
# "coding":[
# {
# "system":"http://www.ihe.net/xds/connectathon/practiceSettingCodes",
# "code":"$setting"
# }
# ]
# },
# "sourcePatientInfo":{
# "reference":"$PatientInfo"
# },
# "related":{
# "reference":"$related"
# }
# }
# }
# }
# ```
# Scenario: Unable to update a Document Pointer when Producer does not have permission
# Given Producer "CUTHBERT'S CLOSE CARE HOME" does not have permission to update Document Pointers for:
# | snomed_code   | description                        |
# | "736253002"   | "Mental health crisis plan"        |
# When Producer "CUTHBERT'S CLOSE CARE HOME" updates an existing current DOCUMENT_POINTER from UPDATE_DOCUMENT template:
# | property          | value                          |
# | identifier        | "1234567890"                   |
# | status            | "current"                      |
# | type              | "736253002"                    |
# | category          | "Counseling note"              |
# | subject           | "Patient/9278693472"           |
# | custodian         | "Organization/f001"            |
# Then the operation is unsuccessful
# And the response contains error message "Required permission to update a document pointer are missing"
# Scenario: Unable to update a Document Pointer when the Producer does not exist
# Given Producer "Lancashire Care" does not exist in the system
# When Producer "Lancashire Care" updates the existing current DOCUMENT_POINTER from UPDATE_DOCUMENT template:
# | property          | value                          |
# | identifier        | "1234567890"                   |
# | status            | "current"                      |
# | type              | "736253002"                    |
# | category          | "Counseling note"              |
# | subject           | "Patient/9278693472"           |
# | custodian         | "Organization/f001"            |
# Then the operation is unsuccessful
# And the response contains error message "Custodian does not exist in the system"
# Scenario: Unable to update a Document Pointer that does not exist
# Given Producer "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL" has permission to update Document Pointers for:
# | snomed_code   | description                        |
# | "736253002"   | "Mental health crisis plan"        |
# And DOCUMENT_POINTER "7852369851" does not exist in the system
# When Producer "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL" updates the DOCUMENT_POINTER "7852369851" from UPDATE_DOCUMENT template:
# | property          | value                          |
# | identifier        | "9876543296"                   |
# | status            | "current"                      |
# | type              | "736253002"                    |
# | category          | "Counseling note"              |
# | subject           | "Patient/9278693472"           |
# | custodian         | "Organization/f001"            |
# Then the operation is unsuccessful
# And the response contains error message "DocumentReference does not exist in the system"
# Scenario Outline: Unable to update the immutable properties of a DOCUMENT_POINTER
# Given Producer "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL" has permission to update Document Pointers for:
# | snomed_code   | description                        |
# | "736253002"   | "Mental health crisis plan"        |
# When Producer "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL" updates an existing current DOCUMENT_POINTER from UPDATE_DOCUMENT template:
# | property      | value                              |
# | <property>    | <value>                            |
# Then the operation is unsuccessful with error "Permission Denied"
# And the response contains error message "ResourceType is immutable"
# Examples:
# | propertyname         | propertyvalue                  |
# | masterIdentifier     | "1234567890"                   |
# | identifier           | "9876543210"                   |
# | status               | "entered-in-error"             |
# | type                 | "34108-1"                      |
# | subject              | "Patient/9628389106"           |
# | date                 | "2022-09-30T12:30:00+01:00"    |
# | custodian            | "Organization/MHT01"           |
# | relation             | "transforms"                   |
# | relationto           | "DocumentReference/7536941082" |
# Scenario: Unable to update a Document Pointer that is superceded
# Given Producer "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL" has permission to update Document Pointers for:
# | snomed_code   | description                           |
# | "736253002"   | "Mental health crisis plan"           |
# And DOCUMENT POINTER "7852369858" exist in the system as status 'superceded'
# When Producer "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL" updates a superceded DOCUMENT_POINTER "1234567894"
# Then the operation is unsuccessful
# And the response contains error message "DocumentReference status is not 'current'"
# Scenario: Unable to update a Document Pointer that is deleted
# Given Producer "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL" has permission to update Document Pointers for:
# | snomed_code   | description                           |
# | "736253002"   | "Mental health crisis plan"           |
# And DOCUMENT POINTER "7852369858" exist in the system as status 'entered-in-error'
# When Producer "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL" updates a deleted DOCUMENT_POINTER "1234567895"
# Then the operation is unsuccessful
# And the response contains error message "DocumentReference status is not 'current'
