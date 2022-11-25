# NRLF

## Overview

This project has been given the name `nrlf` which stands for `National Records Locator (Futures)`, inheriting it's name from the existing product (NRL) as well as the Spine Futures programme (Futures).

This project uses the `nrlf.sh` script to build, test and deploy. This script will ensure that a developer can reproduce any operation that the CI/CD pipelines does, meaning they can test the application locally or on their own deployed dev environment.

The deployment cycle looks like this.

```
install -> unit test -> build -> deploy -> integration test -> tear down
```

The NRLF uses the following cycle during development, which promotes a "fail fast" methodology by moving unit tests to the front of the process ahead of expensive and slow build/deploy/teardown routines.

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
5. [Logging](#logging)
6. [Sandbox deployment with localstack](#sandbox-deployment-with-localstack)
7. [Route 53 & Hosted zones](#route53--hosted-zones)

## Setup

### 1. Prerequisites

- [poetry](https://python-poetry.org/docs/)
- [pyenv](https://github.com/pyenv/pyenv) (this repository uses python 3.9.15)
- jq
- [tfenv](https://github.com/tfutils/tfenv) (this repository uses terraform 1.3.4)

Swagger generation requirements.

- curl
- jre
- yq v4

### 2. Install python dependencies

At the root of the repo, run:

```shell
poetry install
poetry shell
pre-commit install
```

## Initialise shell environment

To use `nrlf` shell script commands. We must initialise the shell environment. Ensure all packages are installed, run the following commands at the root of the repository.

```shell
poetry shell
source nrlf.sh
```

This will enable the `nrlf` commands.

## Login to AWS

To login to AWS, use:

```shell
nrlf aws login <role alias> <mfa token>
```

This reads `~/.aws/config` file. You will need to ensure the config file is setup correctly.

Furthermore, prior to running `nrlf aws login` any time you need to ensure that you've logged out of any previous sessions:

```shell
nrlf aws reset-creds
```

## Build, Test & Run the API

Now we have installed the dependencies we're going to need to get the software up and running.

The API is written in Python, so ensure [Initialise shell environment](#initialise-shell-environment) step is completed

### 1. Run the Unit Tests

The NRLF adopts a "fail fast" methodology, which means that Unit Tests can be run before any expensive operations, such as a complete build or terraform deployment.

```shell
nrlf test unit
```

Note that if you have not configured aws some unit tests will fail. To set the correct aws region for the unit tests.

```shell
aws configure set default.region "eu-west-2"
```

### 2. Deploy the NRLF

The NRLF is deployed using terraform. The infrastructure is split into two parts.

One part contains the main infrastructure, which contains all AWS resources that are not required to be tied to AWS accounts (e.g. lambdas, api gateways etc.). You can find the terraform for NRLF main infrastructure in `terraform/infrastructure`

The second part include resources that should be shared by other resources in the same AWS account. This can include Route 53 hosted zones or IAM roles. You can find the terraform for NRLF account wide infrastructure in `terraform/account-wide-infrastructure`

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

To run feature tests locally

```shell
nrlf test feature local
```

To run feature tests against deployed infrastructure

```shell
nrlf test feature integration
```

## Logging

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

## Sandbox deployment with LocalStack

In order to deploy the entire stack locally we use LocalStack.

💡 You need to install a Docker client on your machine according to the instructions for your OS.

### 1. Setup the virtual environment

As before we need to get the virtual environment running and then re-mount the `nrlf.sh` script:

```shell
poetry install
poetry shell
source nrlf.sh
```

### 2. (re)build the sandbox image

In order to build the sandbox, do:

```shell
nrlf sandbox build
```

### 3. Run the sandbox locally

In order to spin up a sandbox container from the sandbox image, do:

```shell
nrlf sandbox up
```

Note that there is a short wait while the terraform infrastructure is deployed.

You can verify that the sandbox proxy is running with:

```shell
curl http://localhost:8000/_status
```

and you can hit the Consumer and Producer endpoints with:

```shell
curl http://localhost:8000/producer/DocumentReference
curl http://localhost:8000/consumer/DocumentReference
```

and you can run feature tests with:

```shell
nrlf test feature sandbox
```

💡 Note that if you would like to interact with the "AWS" infrastructure in your container you can do so on port 4566, and specifically with `boto3` you can use the keyword argument `endpoint_url=http://localhost:4566` in `boto3.client`. This is the mechanism that our feature tests use to seed data in the dynamodb tables, for example.

### 4. 🚧 Deploy the sandbox on AWS (work in progress) 🚧

Assuming that you have already deployed all of the infrastructure via

```
nrlf terraform plan
```

and

```
nrlf terraform apply
```

then you can deploy the sandbox image to AWS with:

```
nrlf sandbox deploy
```

#### Work in progress instructions:

- In order to activate the sandbox on AWS you must modify the sandbox.tf file so that the memory / n_cpus match the instance_type. For example, setting instance_type to `t3.large` with the current settings will work fine.
- In order to hit the sandbox endpoint you should look up the DNS of the load balancer for the ec2 instance in your sandbox's autoscaling group. Similarly to the local sandbox, you can hit them on port 8000, with endpoints `consumer/DocumentReference` and `producer/DocumentReference`.
- Port 4566 is not enabled
- Outstanding issue: the lambdas in the sandbox (which are docker-in-docker invoked containers) cannot communicate with the main container's dynamodb service. The most portable solution would be to switch to localstack's `local` mode of lambda execution, which we would need to prototype locally first. The more robust solution would be to understand how to get the lambda containers to speak to the main container.

## Route53 & Hosted Zones

There are 2 parts to the Route53 configuration:

### 1. environment accounts

In `terraform/account-wide-infrastructure/prod/route53.tf`, for example, we have a Hosted Zone:

```terraform
resource "aws_route53_zone" "dev-ns" {
  name = "dev.internal.record-locator.devspineservices.nhs.uk"
}
```

### 2. mgmt account

In `terraform/account-wide-infrastructure/mgmt/route53.tf` we have both a Hosted Zone and a Record per environment, for example:

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
