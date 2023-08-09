# Changelog

## 2023-08-03a

- NRLF-491 - Implement int-sandbox splunk environment
- NRLF-525 - Add versioning to firehose S3 bucket
- NRLF-529 - ASDF Tool manager
- NRLF-613 - Increase lambda memory size
- NRLF-638 - Can create documents with contact details
- NRLF-658 - Consumer S3 Auth

## 2023-07-27

- NRLF-526 - CIS2
- NRLF-560 - JSON Schema / Data contracts
- NRLF-640 - Add changelog details to narrative
- NRLF-650 - Dependabot updates
- NRLF-651 - Converter tests
- NRLF-655 - Tag/release fix

## 2023-07-19

- NRLF-586 - Consolidate and publish CHANGELOG.md
- NRLF-460 - Merge steps for search, searchPost and count
- NRLF-599 - SSO
- NRLF-620 - Update the IAM-developer role for mgmt to allow them to call test secrets (done within NRLF-599 branch)
- NRLF-624 - Dependabot part 4 - More updates from the dependabot sorting and merging
- NRLF-627 - The release tag creation mechanism needs to use changelog file

## 2023-07-11a

- NRLF-605 - Update Readme
- NRLF-506 - [MI/BI] DB schema and querying the DB

## 2023-07-06

- NRLF 559 - author is included in set of immutable fields
- NRLF 492 - Use latest change log for release tag
- NRLF 610 - dependabot changes
- NRLF 616 - Added feature test for fully populated NRL pointer

## 2023-06-30

- Fix Count End Point has incorrect parameters (NRLF-577)
- Fix URL in prod smoke tests (NRLF-614)
- Create operation should fail when id(part after '-') has blank or special characters (NRLF-494)

## 2023-06-29

- Remove double hyphen from RDS cluster name

## 2023-06-23

- Authoriser parses headers for authorization into the "request context" to be used by API lambdas
- S3 bucket implemented for authorization lookup where nrl.enable-authorisation-lookup has been set
- All API lambdas read the authorisation from the event "request context" instead of the event headers
- (in nrl-producer-api repo) Update producer apigee proxy to optionally use enable-authorisation-lookup instead of nrl-ods-XXX

## 2023-06-20

- NRLF-522 - errors section in narrative
- NRLF-584 - dependabot changes
- NRLF-564 - strip empty elements

## 2023-06-14

- NRLF-505 - RDS instance, cluster and other terraform and lambda changes for MI/BI
- NRLF-517 - smoke tests that cover the NRL sync functionality
- NRLF-550 - Corrections to the ASID system value

## 2023-06-13

- NRLF-578-dependabot changes

## 2023-05-30

- NRLF-535 - New count endpoint
- NRLF-543 - type.code feature tests
- NRLF-424 - Remove ASID from swagger
- NRLF-482 - Make ID immutable field

## 2023-05-15

- Optimisation of status lambda

## 2023-05-11

- Changes to the onboarding documents
- Changed the duplicateError to return a 409 instead of 400
- Syncing supersede date

## 2023-05-10

- Supersede will not fail on delete for data sync permissions

## 2023-05-03

- Firehose error alerts
- Superseding of created_on and when caller has permission audit-dates-from-payload

## 2023-05-02

Security enhancements:

- Deletion protection on DynamoDB
- Dependabot improvements

## 2023-04-30

- Fix Count End Point has incorrect parameters
- Fix URL in prod smoke tests
- Create operation should fail when id(part after '-') has blank or special characters

## 2023-04-25

- Multiple End-User organisations support
- Logging improvements
- Build improvements
- Authentication improvements
