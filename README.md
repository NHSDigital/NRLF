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
