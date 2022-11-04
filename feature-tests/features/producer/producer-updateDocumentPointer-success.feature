# Feature: Success scenarios where producer is able to update a Document Pointer
# Background:
# Given the following DOCUMENT_POINTER exists:
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
# Scenario: Successfully update the category of an existing Document Pointer
# Given Producer "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL" has permission to update Document Pointers for:
# | snomed_code       | description                    |
# | "736253002"       | "Mental health crisis plan"    |
# When Producer "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL" updates the existing DOCUMENT_POINTER from UPDATE_DOCUMENT template:
# | property          | value                          |
# | identifier        | "1234567890"                   |
# | status            | "current"                      |
# | type              | "736253002"                    |
# | category          | "Counseling note"              |
# | subject           | "Patient/9278693472"           |
# | custodian         | "Organization/f001"            |
# Then the operation is successful
# And Document Reference "1234567890" exists for Producer "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL" as:
# | category          | "Counseling note"              |
# Scenario Outline: Successfully update the mutable properties of a Document Pointer
# Given Producer "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL" has permission to update Document Pointers for:
# | snomed_code       | description                    |
# | "736253002"       | "Mental health crisis plan"    |
# When Producer "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL" updates the existing DOCUMENT_POINTER from UPDATE_DOCUMENT template:
# | property          | value                          |
# | identifier        | "1234567890"                   |
# | status            | "current"                      |
# | type              | "736253002"                    |
# | subject           | "Patient/9278693472"           |
# | custodian         | "Organization/f001"            |
# | <property>        | <value>                        |
# Then the operation is successful
# And the response contains success message "Resource updated"
# And Document Reference "1234567890" exists for Producer "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL" as:
# | <property>        | <value>                        |
# Examples:
# | property             | value                                              |
# | docStatus            | "amended"                                          |
# | author               | "Organization/1XR"                                 |
# | authenticator        | "Organization/MHT01"                               |
# | description          | "Therapy Summary Document for Patient 9278693472"  |
# | securityLabel        | "very restricted"                                  |
# | location             | "https://example.org/my-doc-updated.pdf"           |
# | language             | "en-US"                                            |
# | contenttype          | "application/hl7-v3+xml"                           |
# | format               | "urn:nhs:TEXT"                                     |
# | encounter            | "Encounter/OBSENC"                                 |
# | event                | "mental health history record"                     |
# | period               | "2022-09-30T12:30:00+01:00"                        |
# | facility             | "Outpatient"                                       |
# | setting              | "Adult mental health service"                      |
# | patientInfo          | "9628389106"                                       |
# | related              | "7536941082"                                       |
