# NRLF

## Overview

This project has been given the name `nrlf` which stands for `National Records Locator (Futures)` as a replacement of the existing NRL.

This project uses the `nrlf.sh` script to build, test and deploy. This script will ensure that a developer can reproduce any operation that the CI/CD pipelines does, meaning they can test the application locally or on their own deployed dev environment.

## Table of Contents

1. [Setup](#setup)
   1. [Prerequisites](#1-prerequisites)
   2. [Install python dependencies](#2-install-python-dependencies)
2. [Initialise shell environment](#initialise-shell-environment)
3. [Login to AWS](#login-to-aws)
4. [Build, Test & Run the API](#build-test--run-the-api)
   1. [Run unit tests](#1-run-the-unit-tests)
   2. [Deploy NRLF](#2-deploy-the-nrlf)
   3. [Run integration tests](#3-run-the-integration-tests)
   4. [Run feature tests](#4-run-the-feature-tests)
   5. [Feature test rules](#5-feature-test-rules)
5. [Smoke tests and oauth tokens for Postman requests](#smoke-tests-and-oauth-tokens)
6. [Logging](#logging)
7. [Route 53 & Hosted zones](#route53--hosted-zones)
8. [Sandbox](#sandbox)
9. [Firehose](#firehose)
10. [Releases](#releases)
11. [MI reporting](#mi-reporting)

---

## Setup

Before you tackle this guide, there are some more instructions here on the [Developer onboarding guide](https://nhsd-confluence.digital.nhs.uk/pages/viewpage.action?spaceKey=CLP&title=NRLF+-+Developer+Onboarding) in confluence

### 1. Prerequisites

- [poetry](https://python-poetry.org/docs/)
- [pyenv](https://github.com/pyenv/pyenv) (this repository uses python ^3.9.15)
- jq
- terraform
- [tfenv](https://github.com/tfutils/tfenv) (this repository uses terraform 1.3.4)
- coreutils

Swagger generation requirements.

- curl
- java runtime environment (jre) - https://www.oracle.com/java/technologies/downloads/#jdk19-mac
- yq v4

### 2. Linux set up

For those on a linux/WSL setup these are some helpful instructions:

- We recommend that you use the NRLF with VSCode and WSL rather than the Spine VM
- There is also a plugin for VSCode called `WSL` which will help you avoid some terminal issues when opening projects in WSL

#### 1. Java:

```shell
sudo apt install default-jre
```

#### 2. Poetry:

```shell
curl -sSL https://install.python-poetry.org | python3
```

```shell
nano ~/.bashrc
```

add to bashrc - spineVM home dir is "/home/spineii-user/"

```shell
export PATH="/$HOME/.local/bin:$PATH"
```

```shell
source ~/.bashrc
```

```shell
poetry --version
```

#### 3. pyenv:

```shell
sudo apt-get update; sudo apt-get install make build-essential libssl-dev zlib1g-dev \
libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm \
libncursesw5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev
```

```shell
curl https://pyenv.run | bash
```

```shell
nano ~/.bashrc
```

add to bashrc

```shell
export PATH="$HOME/.pyenv/bin:$PATH"
eval "$(pyenv init --path)"
eval "$(pyenv virtualenv-init -)"
```

```shell
source ~/.bashrc
```

```shell
pyenv --version
```

#### 4. terraform

```shell
wget -O- https://apt.releases.hashicorp.com/gpg | gpg --dearmor | sudo tee /usr/share/keyrings/hashicorp-archive-keyring.gpg
```

```shell
echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
```

```shell
sudo apt update && sudo apt install terraform
```

#### 5. tfenv:

Manual:

```shell
git clone https://github.com/tfutils/tfenv.git ~/.tfenv
```

---

IF YOU ARE WSL RUN COMMAND BELOW THIS ONE

```shell
echo 'export PATH="$HOME/.tfenv/bin:$PATH"' >> ~/.bash_profile
```

For WSL users

```shell
echo 'export PATH=$PATH:$HOME/.tfenv/bin' >> ~/.bashrc
```

---

```shell
sudo ln -s ~/.tfenv/bin/* /usr/local/bin
```

```shell
tfenv --version
```

#### 6. yq:

```shell
sudo wget https://github.com/mikefarah/yq/releases/latest/download/yq_linux_amd64 -O /usr/bin/yq && sudo chmod +rx /usr/bin/yq
```

### 2. Install python dependencies

At the root of the repo, run:

```shell
poetry install
poetry shell
pre-commit install
```

NOTE

- You will know if you are correctly in the shell when you see the following before your command line prompt `(nrlf-api-py3.11)` (the version may change based on the version of python)
- If it says (.venv) then you are not using the correct virtual environment
- As mentioned above you at least need Python 3.9 installed globally to run the project, Poetry will handle the rest
- The terraform version can be found in the .terraform-version file at the root

---

## Quick Run

For those wanting to get up and running quickly can follow this list of instructions which by the end will have given you your own workspace with the current version of NRLF running - you can find more information on steps below this section.

```shell
poetry shell
source nrlf.sh
nrlf make build
nrlf aws reset-creds
nrlf aws login mgmt
nrlf truststore pull-server dev
nrlf truststore pull-client dev
nrlf terraform plan <yourname>-test
nrlf terraform apply <yourname>-test
nrlf test feature integration
nrlf terraform destroy <yourname>-test
```

---

## Initialise shell environment

```shell
poetry shell
source nrlf.sh
```

This will enable the `nrlf` commands.

## Login to AWS

To login to AWS, use:

```shell
nrlf aws reset-creds
```

To ensure you werent logged into a previous session

```shell
nrlf aws login <env> <mfa token>
```

The env options are `dev, mgmt, test and prod`

This reads the `~/.aws/config` file. You will need to ensure the config file is setup correctly - see [Developer Onboarding](https://nhsd-confluence.digital.nhs.uk/display/CLP/NRLF+-+Developer+Onboarding).

## Build, Test & Run the API

Now we have installed the dependencies we're going to need to get the software up and running.

### 1. Run the Unit Tests

```shell
nrlf test unit
```

Note that if you have not configured aws some unit tests will fail. To set the correct aws region for the unit tests.

```shell
aws configure set default.region "eu-west-2"
```

### 2. Deploy the NRLF

The NRLF is deployed using terraform. The infrastructure is split into two parts.

All account wide resources like Route 53 hosted zones or IAM roles are found in `terraform/account-wide-infrastructure`

All resources that are not account specific (lambdas, API gateways etc) can be found in `terraform/infrastructure`

Information on deploying these two parts:

- [NRLF main infrastructure](./terraform/infrastructure/README.md)
- [NRLF account wide infrastructure](./terraform/account-wide-infrastructure/README.md)

### 3. Run the Integration Tests

Once the environment has been deployed the integration tests can be run.

```shell
nrlf test integration
```

This executes any tests that have been marked with `@pytest.mark.integration`

### 4. Run the Feature Tests

Feature tests are environment agnostic. They can either be run against local code or against the deployed infrastructure.

You can run feature tests using the command:

```shell
nrlf test feature <enviroment>
```

To run feature tests locally

```shell
nrlf test feature local
```

To run feature tests against deployed infrastructure

```shell
nrlf test feature integration
```

You can also run individual tests by getting the Scenario name of the feature test and inserting it in the following command:

```shell
python -m behave feature_tests -n '<feature test name>' -D "integration_test=true"
```

It is also possible to run a suite of tests by using the `-i` command:

```shell
python -m behave  --define="integration_test=true" -i '<name of feature test suite file>' ./feature_tests/
```

you can also use the `-i` command for fuzzy matching like so:

```shell
python -m behave --define="integration_test=true" -i '.*producer*' ./feature_tests/
```

this will run all the producer integration tests.

### 5. Feature test rules

Referring to the sample feature test below:

```gherkin
Scenario: Successfully create a Document Pointer of type Mental health crisis plan
   Given {ACTOR TYPE} "{ACTOR}" (Organisation ID "{ORG_ID}") is requesting to {ACTION} Document Pointers
   And {ACTOR TYPE} "{ACTOR}" is registered in the system for application "APP 1" (ID "{APP ID 1}") for document types
     | system                  | value     |
     | http://snomed.info/sct | 736253002 |
   And {ACTOR TYPE} "{ACTOR}" has authorisation headers for application "APP 2" (ID "{APP ID 2}")
   When {ACTOR TYPE} "{ACTOR}" {ACTION} a Document Reference from DOCUMENT template
     | property    | value                          |
     | identifier  | 1234567890                     |
     | type        | 736253002                      |
     | custodian   | {ORG_ID}                       |
     | subject     | 9278693472                     |
     | contentType | application/pdf                |
     | url         | https://example.org/my-doc.pdf |
   Then the operation is {RESULT}
```

The following notes should be made:

1. ACTOR TYPE, ACTOR and ACTION are forced
   to be consistent throughout your test
2. ACTOR TYPE, ACTOR, ACTION, ORG_ID, APP, APP ID, and
   RESULT are enums: their values are
   restricted to a predefined set
3. ACTOR is equivalent to to both custodian
   and organisation
4. The request method (GET, POST, ...) and
   slug (e.g. DocumentReference/\_search) for
   ACTION is taken from the swagger.
5. ”Given ... is requesting to” is mandatory:
   it sets up the base request
6. ”And ... is registered to” sets up a
   org:app:doc-types entry in Auth table
7. ”And ... has authorisation headers” sets up
   authorisation headers

---

## Smoke tests and OAuth tokens

### Smoke tests

You can run smoke tests from the CLI using:

```
nrlf test smoke {actor} {env} {app_alias}
```

where `app_alias` is either `default` or `nrl_sync`. If you omit `app_alias`, it will anyway default to `default`.

If you want to utilise the sandbox then you need to put that on the end of the env command - example below

```
nrlf test smoke producer dev-sandbox
```

This will run an end-to-end test against the environment/workspace via Apigee that you designated.

---

### OAUTH tokens for requests

All clients to the NRLF require tokens to connect through apigee - we can replicate this to test the persistent environments using this command to generate a token:

```
nrlf oauth {env} {app_alias}
```

where `app_alias` is either `default` or `nrl_sync`. If you omit `app_alias`, it will anyway default to `default`.

Some examples:

```
nrlf oauth dev
nrlf oauth dev default  # Note: this is the same as above
nrlf oauth dev nrl_sync
nrlf oauth int
nrlf oauth int nrl_sync
```

Other valid environments in addition to `dev` are `int`, `ref` and `prod` (reminder that int and ref exist within the test account).

This command will print out an OAuth `<token>` which can be used in a request to our Apigee endpoint as a header of the form:

```
Authorization: Bearer <token>
```

---

## Logging

This project implements action-based logging. If you want to log a function you must decorate your function with:

```python
from enum import Enum
from lambda_utils.logging import log_action

class LogReference(Enum):
   READ001 = "Reading a document"

@log_action(log_reference=LogReference.READ001, log_fields=["id"], sensitive=False)
def read_a_document(id, something_i_dont_want_shared):
    ...
```

💡 Only fields specified in `log_fields` will be logged.

To activate logging for your decorated function you need to pass in an instance of `lambda_utils.logging.Logger`:

```python
logger = Logger(...)  # Read the docs for the required fields
read_a_document(id=123, something_i_dont_want_shared="xxxx", logger=logger)
```

`log_action` enables an extra argument `logger` for `read_a_document`, which will be stripped by default before executing your function `read_a_document`.

💡 Don't worry if your function already has an argument named `logger`, it will be retained if you defined it to be there.

Other notes:

- All logs are considered sensitive unless otherwise stated: explicitly setting `sensitive=False` will enable the log in question to flow through to the non-sensitive Splunk indexes.
- The function / action result can be excluded with `log_action(..., log_result=False, ...)`
- If the function / action outcome leads to a 4XX error, it is treated with outcome `FAILURE` and the result is the raised error .
- If the function / action outcome leads to a 5XX error, it is treated with outcome `ERROR` and the `call_stack` and `error` are also returned.

### Sample log from above example

```json
{
  "correlation_id": "abasbee3-c461-4bc6-93f0-95c2ee7d3aab",
  "nhsd_correlation_id": "cbbbab64-c461-4bc6-93f0-95c2ee7d3aab",
  "transaction_id": "a3278113-38c6-4fcc-8d25-7b1bda4e1c64",
  "request_id": "daas23e3-c461-4bc6-93f0-95c2ee7d3aab",
  "environment": "a4081ca6",
  "sensitive": false,
  "log_level": "INFO",
  "log_reference": "my.example.module.read_a_document",
  "outcome": "SUCCESS",
  "duration_ms": 258,
  "message": "Reading a document",
  "data": {
    "result": "Lorem ipsum",
    "inputs": { "id": 123 }
  },
  "timestamp": "2022-11-08T16:39:00.090Z"
}
```

### Firehose and Splunk

Logs are processed by Firehose and forwarded to:

- S3 for development and CI terraform workspaces (Firehose destination "extended_s3")
- Splunk for persistent environments workspaces (Firehose destination "splunk")

To enable Splunk for a given workspace, ensure that Splunk connection credentials have been set in the corresponding AWS secret resource (see firehose terraform module for more details). You will also need to set 'destination = "splunk"' in the initialisation of the Firehose terraform module, but do not merge this into production since we don't want all development workspace logs going to Splunk. (Our test suite will anyway reject this in the CI, since it expects that the "extended_s3" has been used for non persistent environments)

More details about Firehose are given below.

---

## Route53 & Hosted Zones

There are 2 parts to the Route53 configuration:

### 1. environment accounts

In `terraform/account-wide-infrastructure/prod/route53.tf`, we have a Hosted Zone:

```terraform
resource "aws_route53_zone" "dev-ns" {
  name = "dev.internal.record-locator.devspineservices.nhs.uk"
}
```

### 2. mgmt account

In `terraform/account-wide-infrastructure/mgmt/route53.tf` we have both a Hosted Zone and a Record per environment:

```terraform
resource "aws_route53_zone" "prodspine" {
  name = "record-locator.spineservices.nhs.uk"

  tags = {
    Environment = terraform.workspace
  }
}

resource "aws_route53_record" "prodspine" {
  zone_id = aws_route53_zone.prodspine.zone_id
  name    = "prod.internal.record-locator.spineservices.nhs.uk"
  records = ["ns-904.awsdns-49.net.",
    "ns-1539.awsdns-00.co.uk.",
    "ns-1398.awsdns-46.org.",
    "ns-300.awsdns-37.com."
  ]
  ttl  = 300
  type = "NS"
}
```

The `records` property is derived by first deploying to a specific environment, in this instance, production, and from the AWS Console navigating to the Route53 Hosted Zone that was just deployed and copying the "Value/Route traffic to" information into the `records` property. Finally, deploy to the mgmt account with the new information.

---

## Sandbox

The public-facing sandbox is an additional persistent workspace (`int-sandbox`) deployed in our UAT (`int` / `test`) environment, alongside the persistent workspace named `ref`. It is identical to our live API, except it is open to the world via Apigee (which implements rate limiting on our behalf).

### Sandbox deployment

In order to deploy to a sandbox environment (`dev-sandbox`, `ref-sandbox`, `int-sandbox`, `production-sandbox`) you should use the GitHub Action for persistent environments, where you should select the option to deploy to the sandbox workspace.

### Sandbox database clear and reseed

Any workspace suffixed with `-sandbox` has a small amount of additional infrastructure deployed to clear and reseed the DynamoDB tables (auth and document pointers) using a Lambda running
on a cron schedule that can be found in the `cron/seed_sandbox` directory in the root of this project. The data used to seed the DynamoDB tables can found in the `cron/seed_sandbox/data` directory.

Even though you probably won't need to (since there is local end-to-end testing), if you would like to test this Lambda in AWS then you can deploy it using a workspace name thats suffixed with "-sandbox" - e.g "test123-sandbox":

```
nrlf make build
nrlf terraform plan test123-sandbox
nrlf terraform apply test123-sandbox
```

The Lambda does not expect any arguments, so you can invoke the Lambda directly on the console using a blank (`{}`) test event.

Don't forget to clean up once you're done:

```
nrlf terraform destroy test123-sandbox
```

### Sandbox authorisation

The configuration of organisations auth / permissions is dealt with in the "apigee" repos, i.e.

- https://github.com/NHSDigital/record-locator/producer
- https://github.com/NHSDigital/record-locator/consumer

Specifically, the configuration can be found in the file proxies/sandbox/apiproxy/resources/jsc/ConnectionMetadata.SetRequestHeaders.js in these repos.

💡 Developers should make sure that these align between the three repos according to any user journeys that they envisage.

Additionally, and less importantly, there are also fixed organization details in proxies/sandbox/apiproxy/resources/jsc/ClientRPDetailsHeader.SetRequestHeaders.js in these repos.

## Firehose

### tl;dr

- All Firehose errors must be investigated since (in the worst case, but not unlikely scenario) they may block all logs from reaching Splunk.
- The main NRLF repo contains a tool to help with debugging, but it cannot diagnose the problem for you.
- Bad logs = bad code: so please fix the code to prevent this from reoccurring
- Any good logs which have been blocked must be manually resubmitted, we have a tool to help with that too.
- You may also need to fix bad logs prior to resubmission if required.

### Background

As illustrated in [NRLF - Logging Solution](https://nhsd-confluence.digital.nhs.uk/display/CLP/NRLF+-+Logging+Solution), the API logs are piped from Cloudwatch to Splunk via Firehose. Unfortunately Firehose lambdas are unnecessarily complex, and correspondingly have a complex nested data model as illustrated in Figure X. An individual Firehose Event is composed of Firehose Records, which each Record containing a single Cloudwatch Logs Data object, which contains multiple Log Events. The Firehose Lambda marks Firehose Records as being "OK" or "FAILED", with OK Records being sent to Splunk and FAILED Records landing in the Firehose bucket under the "errors" prefix. Therefore (without the improvement suggested in NRLF-385) any single bad Log Event will cause all Log Events in the Record to be collectively marked as FAILED.

### Resolving failures

In order to understand the debugging lifecycle, please follow this example and then adapt to your real use-case:

1. Run `nrlf test firehose`
2. wait five minutes until the test is complete
3. go to s3 and get the s3 URI of the most recent file in the firehose S3 bucket with the prefix `errors/`
4. Run `nrlf fetch s3_uri <env>` (default <env> is `dev` i.e. don't need to set this if testing in your own workspace)
5. Follow the instructions from `fetch` in order to resubmit the file
   1. Run `nrlf validate file_path`
   2. Remove lines 3 and 7 from the bad file
   3. Run `nrlf validate file_path`
   4. Run `nrlf resubmit file_path <env>` (<env> should match the value from line 4)
6. Verify that the file has been moved from `errors/` to `fixed/` on s3

## Releases

When you create a release branch in the form of `release/yyyy-mm-dd` or `hotfix/yyyy-mm-dd` then you need to update the RELEASE file in the top level of the repository to match that release name

The CI pipeline will check to make sure you have done this to prevent any mistakes - if you have made a release or hotfix branch it will check that the value in the RELEASE file matches or not

This is because it will use that value to tag the commit once its been merged into main as a reference point, and this is how it tracks which release it is as github actions struggles with post merge branch identification

## Generating MI reports

MI reports can be generated in CSV format by running:

```
nrlf mi report <env> <?workspace> <?partition_key>
```

For standard reports, both `workspace` and `partition_key` can be omitted, however for testing purposes you should `workspace`. If you would like to use test data (found in `mi/reporting/tests/test_data/test_data.json`) then you can do:

```
nrlf mi seed-db <partition_key>
```

which will seed an amended version of the test data into the database for your current workspace, which uses the `partition_key` to make the test data unique. You can then run the previous `nrlf mi report` command with your `workspace` and `partition_key` to build reports based on the test data.

All reports, test or otherwise, are saved to `mi/reporting/report`.

### Creating or amending report queries

Report queries are SQL files that can be found in `mi/reporting/queries`. The standard (pytest, i.e. not gherkin) integration tests will test all reports based on the test data, and will also provide regex validation using matching files found under `mi/reporting/queries/test_validation`.

For example, if a report query file `mi/reporting/queries/my_report.sql` exists, then a corresponding validation file is also expected to exist called `mi/reporting/queries/test_validation/my_report.yaml` with the form:

```yaml
field_1: ^\w+$ # field called "field_1" which contains alphanumeric string
field_2: ^\d+$ # field called "field_2" which contains a positive integer
```
