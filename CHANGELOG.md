# Changelog

## 2024-01-09

- NRLF-657 Add workspace destroy and unlock commands
- SPINECLI-1665 Add asid-check data contract for the new pointer type Lloyd george
- NRLF-708 Fix sonarcloud security hotspot changes
- SPINECLI-1704 add checks and cleanup to contract integration tests
- NRL-445 Add Allure reports
- SPINECLI-1666 Documentation Updates

## 2023-10-26

- SPINECLI-1611 - Create sonar-project.properties file for SonarCloud configuration

## 2023-10-09

- SPINECLI-1090 - Update NRLF Readme with WSL and Powershell Instructions
- SPINECLI-1619 - Change the readme - updated section on Reporting to add more info

## 2023-09-21

- SPINECLI-1190 - Add link to postman collection in narrative
- NRLF-691 - Amend Document Type used in NRLF Smoke Test to clearly identify as Test-Only in MI Reports
- SPINECLI-1043 - 403 when x-correlation-id or x-request-id is missing

## 2023-09-13

- NRLF-696 - BUG: MI report date range
- NRLF-697 - Enhancement: MI Max Year
- NRLF-702 - Add Postman Collection to API Catalogue

## 2023-09-06

- NRLF-644 - Add missing "Errors" to swagger response in Consumer.
- NRLF-646 - Add missing "Errors" to swagger response in Producer.
- NRLF-663 - Add Open Source section to Producer/Consumer Narrative
- NRLF-693 - Sonarcube Fixes
- NRLF-682 - Remove documentation from CI
- NRLF-698 - Fix Forward: 4XX isn’t valid in API Gateway
- NRLF-582 - (APIGEE) 64L CORS issue with "TRY" Section in API Catalogue
- NRLF-690 - (APIGEE) Update dependency

## 2023-08-29

- NRLF-563 - 64L Sort fields that should be treated as Sets, not ordered Lists
- NRLF-675 - MI dead letters, resubmission and alerting
- NRLF-683 - MI Documentation and reports
- NRLF-689 - Update NRLF 1D Converter to v0.0.9
- Dependabot updates:
  - pydantic (1.10.10 -> 1.10.12)
  - boto3 (1.26.165 -> 1.28.30)
  - cryptography (41.0.1 -> 41.0.3)
  - awscli (1.27.165 -> 1.29.30)
  - datamodel-code-generator (0.21.2 -> 0.21.4)
  - cookiecutter (2.2.3 -> 2.3.0)
  - atlassian-python-api (3.39.0 -> 3.41.0)
  - hypothesis (6.82.0 -> 6.82.6)
  - more-itertools (9.1.0 -> 10.1.0)

## 2023-08-21

- NRLF-669 - Changelog now uses rendered markdown
- NRLF-653 - Producer MI - Create data model and insert into database
- NRLF-583 - Remove 'newman' from APIGEE proxies (APIGEE repos only)

## 2023-08-16

- NRLF-561 - Fix forward: Add missing NEWS2 document type data contract

## 2023-08-14

- NRLF-533 - 409 Conflict error not thrown on duplicate supersede request
- NRLF-585 - Add Live URLs to API Catalogue
- NRLF-652 - Producer MI - Add infrastructure for dynamodb streams
- NRLF-561 - Build an ASID specific document contract
- NRLF-634 - Helper script to create Data Contracts
- NRLF-642 - Update converter to v0.0.8 in NRLF repository
- NRLF-652 - Fix forward: Remove tags from security groups associations
- NRLF-561 - Fix forward: Fix ASID url
- NRLF-634 - Fix forward: Fix intermittent deploy contract test
- NRLF-494 - Fix forward: Revert changes introduced by NRLF-494, due to being too restrictive for converter

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
