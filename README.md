# NRLF

# Overview

This project has been given the name `nrlf` which stands for `National Records Locator (Futures)`, inheriting it's name from the existing product (NRL) as well as the Spine Futures programme (Futures).

This project uses the `nrlf.sh` script to build, test and deploy. This script will ensure that a developer can reproduce any operation that the CI/CD pipelines does, meaning they can test the application locally or on their own deployed dev environment.

The deployment cycle looks like this.

```
install -> unit test -> build -> deploy -> integration test -> tear down
```

The NRLF uses the following cycle during development, which promotes a "fail fast" methodology by moving unit tests to the front of the process ahead of expensive and slow build/deploy/teardown routines.

# Setup

## Prerequisites

- poetry
- python 3.9
- terraform
- jq
- tfenv

Swagger generation requirements.

- curl
- jre
- yq v4

## Install python dependencies

```
poetry install
poetry shell
pre-commit install
```

## Project CLI and AWS login

These instructions assume that you have enabled the project CLI:

```
source nrlf.sh
```

Furthermore, prior to running `nrlf aws login` any time you need to ensure that you've logged out of any previous sessions:

```
nrlf aws reset-creds
```

# Build, Test & Run the API

Now we have installed the dependencies we're going to need to get the software up and running.

## 1. Setup the virtual environment

The API is written in Python, so we need to get the virtual environment running and then re-mount the `nrlf.sh` script.

```
poetry shell
source nrlf.sh
```

## 2. Run the Unit Tests

The NRLF adopts a "fail fast" methodology, which means that Unit Tests can be run before any expensive operations, such as a complete build or terraform deployment.

```
nrlf test unit
```

Note that if you have not configured aws some unit tests will fail. If you want to run the unit tests without configuring aws, you will have to run:

```
aws configure
```

press enter several times without modifying anything except to set the region to `eu-west-2`

## 2. Build the API

Now build the artifacts that will be used to deploy the application.

```
nrlf make build
```

## 3. Login to AWS

In order to deploy the NRLF you will need to be able to login to the AWS account using MFA.

```
nrlf aws login mgmt-admin <mfa code>
```

## 4. Deploy the NRLF

The NRLF is deployed using terraform, and can be deployed to any number of environments, such as, but not limited to `dev`, `test`, `uat`, `pre-prod`, `production`.

If you do not supply an `<env>` then a hashed key unique to your environment will be generated.

```
nrlf terraform plan [<env>]
```

```
nrlf terraform apply [<env>]
```

## 5. Run the Integration Tests

Once the environment has been deployed the integration tests can be run.

```
nrlf test integration
```

This executes any tests that have been marked with `@pytest.mark.integration`

## 6. Run the Feature Tests

```
nrlf test feature
```

This executes any tests that have been marked with `@integration`

## 7. Tear down

Using the same `<env>` from the deployment stage you can tear down the environment you created.

```
nrlf terraform destroy [<env>]
```

# Create / update account-wide resources

This is for resources such as Cloudwatch roles which are global to a given account instead of a workspace.
Account wide resources should be deployed manually and not be run as part of CI.

Log in to your `mgmt` account.

```shell
nrlf aws login mgmt-admin
```

Update account wide resources for accounts (e.g. `dev`, `test`, `prod`, `mgmt`)

Initialise terraform

```shell
nrlf terraform init <account> account_wide
```

Create a terraform plan

```shell
nrlf terraform plan <account> account_wide
```

Apply changes

```shell
nrlf terraform apply <account> account_wide
```

To teardown account wide resources

```shell
nrlf terraform destroy <account> account_wide
```

# Logging

This project implements action-based logging. In order to use this, you must decorate any function (i.e. your "action") with the `lambda_utils.logging.log_action` decorator:

```python
from lambda_utils.logging import log_action

@log_action(narrative="Reading a document", log_fields=["id"], sensitive=False)
def read_a_document(id, something_i_dont_want_shared):
    ...
```

💡 Only fields specified in `log_fields` will be logged.

To run your decorated function as normal (i.e. without logging) then simply run it is normal:

```python
read_a_document(id=123, something_i_dont_want_shared="xxxx")
```

To activate logging for your decorated function you just need to pass in an instance of `lambda_utils.logging.Logger`:

```python
logger = Logger(...)  # Read the docs for the required fields
read_a_document(id=123, something_i_dont_want_shared="xxxx", logger=logger)
```

As you can see above, `log_action` has enabled an extra argument `logger` for `read_a_document`, which will be stripped by default before executing your function `read_a_document`.

💡 Don't worry if your function already has an argument named `logger`, it will be retained if you defined it to be there.

Other notes:

- All logs are considered sensitive unless otherwise stated: explicitly setting `sensitive=False` will enable the log in question to flow through to the non-sensitive Splunk indexes.
- The function / action result can be excluded with `log_action(..., log_result=False, ...)`
- If the function / action outcome leads to a 4XX error, it is treated with outcome `FAILURE` and the result is the raised error .
- If the function / action outcome leads to a 5XX error, it is treated with outcome `ERROR` and the `call_stack` and `error` are also returned.

## Sample log from above example

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

# Sandbox deployment with LocalStack

In order to deploy the entire stack locally, we use LocalStack which comes bundled with the `dev` dependencies for this project.
You will however need to install a Docker client on your machine according to the instructions for your OS.

## 1. Setup the virtual environment

As before we need to get the virtual environment running and then re-mount the `nrlf.sh` script.

```
poetry shell
source nrlf.sh
```

## 1. (re)build the API

In order to pick up any changes to the API we should build the artifacts that will be used to deploy the application as before:

```
nrlf make build
```

## 2. Synchronise the build to the sandbox

Since the free tier of LocalStack doesn't support layers, we also amend the artifacts to bundle the layers into the main Lambda.

```
nrlf sandbox sync
```

## 3. Deploy the API to LocalStack via Terraform

```
nrlf sandbox deploy
```

Note down any URLs provided in this step, as you will be able to run queries against them.

## 4. Seed the Sandbox database with some test data

In order to enable users to run queries against the Sandbox API, we need to seed the database with some test data:

```
nrlf sandbox seed_db
```

## Project bootstrap

### Setup mgmt account resources

```
🚨 ------------------------------------------------ 🚨
This should only be performed on project setup, and never again.
🚨 ------------------------------------------------ 🚨
```

This will set up your terraform state buckets and import them into your project.

Log in to your `mgmt` account:

```
nrlf aws login mgmt-admin
```

Create resources on mgmt account required for terraform to work. This includes:

- terraform state bucket
- terraform state lock table
- secret managers to hold account ids for the non-mgmt accounts

```
nrlf bootstrap create-mgmt
```

Now log on to AWS web console and manually add the aws account ids to each respective secrets
`nhsd-nrlf--mgmt--mgmt-account-id`, `nhsd-nrlf--mgmt--prod-account-id`, `nhsd-nrlf--mgmt--test-account-id` and `nhsd-nrlf--mgmt--dev-account-id`

### Create trust role for `mgmt` for your non-`mgmt` accounts

```
🚨 ------------------------------------------------ 🚨
This should only be performed on setup of new non-mgmt accounts, and never again.
🚨 ------------------------------------------------ 🚨
```

In order to allow `mgmt` to create resources in non-`mgmt` accounts you
need to create a trust role in non-`mgmt`.

Log in to your non-`mgmt` account (e.g. `dev`):

```
nrlf aws login <non-mgmt-account>-admin
```

Create the trust role:

```
nrlf bootstrap create-non-mgmt
```

# Route53 & Hosted Zones

There are 2 parts to the Route53 configuration:

## 1. environment accounts

In `terraform/account-wide-infrastructure/prod/route53.tf`, for example, we have a Hosted Zone:

```
resource "aws_route53_zone" "dev-ns" {
  name = "dev.internal.record-locator.devspineservices.nhs.uk"
}
```

## 2. mgmt account

In `terraform/account-wide-infrastructure/mgmt/route53.tf` we have both a Hosted Zone and a Record per environment, for example:

```
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
