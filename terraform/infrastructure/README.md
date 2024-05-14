# NRLF main infrastructure

This directory contains terraform to build the main NRLF api infrastructure.

NRLF project uses terraform workspaces to handle multiple "environments". Environments are identified by their workspace id. Resources in each environment will contain workspace id in its name. (e.g. nhsd-nrlf--dev--document-pointer or nhsd-nrlf--469d5da6--document-pointer)

Each developer/QA can create their own instance of NRLF infrastructure. These are deployed to the dev AWS account and use variables in `etc/dev.tfvars`

This project also uses "persistent environments". These are equivalent to traditional dev, ref and prod environments. The persistent environments are deployed as follows:

| Environment  | TF Workspace | TF Config         | AWS Account | Internal Domain                      | Public Domain                             |
| ------------ | ------------ | ----------------- | ----------- | ------------------------------------ | ----------------------------------------- |
| internal-dev | dev          | `etc/dev.tfvars`  | dev         | `record-locator.dev.national.nhs.uk` | `internal-dev.api.service.nhs.uk`         |
| dev-sandbox  | dev-sandbox  | `etc/dev.tfvars`  | dev         | `record-locator.dev.national.nhs.uk` | `internal-dev-sandbox.api.service.nhs.uk` |
| internal-qa  | qa           | `etc/qa.tfvars`   | test        | `qa.record-locator.national.nhs.uk`  | `internal-qa.api.service.nhs.uk`          |
| qa-sandbox   | qa-sandbox   | `etc/qa.tfvars`   | test        | `qa.record-locator.national.nhs.uk`  | `internal-qa-sandbox.api.service.nhs.uk`  |
| int          | int          | `etc/int.tfvars`  | test        | `record-locator.int.national.nhs.uk` | `int.api.service.nhs.uk`                  |
| sandbox      | int-sandbox  | `etc/int.tfvars`  | test        | `record-locator.int.national.nhs.uk` | `sandbox.api.service.nhs.uk`              |
| ref          | ref          | `etc/ref.tfvars`  | test        | `record-locator.ref.national.nhs.uk` | `ref.api.service.nhs.uk`                  |
| prod         | prod         | `etc/prod.tfvars` | prod        | `record-locator.national.nhs.uk`     | `api.service.nhs.uk`                      |

CI pipeline creates infrastructure in the test AWS account. These will have workspace id of `<first six char of commit hash>-ci` and use variables in `etc/test.tfvars`

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Deploy infrastructure](#deploy-infrastructure)
3. [Teardown infrastructure](#teardown-infrastructure)

## Prerequisites

Before you begin deploying NRLF infrastructure, you will need:

- An NRLF-enabled AWS account, ideally `dev`. See [bootstrap](../bootstrap/README.md) for details on setting up a new account.
- The required packages to build NRLF, see [the Setup section in README.md](../../README.md#setup).
- To be logged into the AWS mgmt account on the CLI that you are deploying from.

If infrastructure changes require account wide AWS resources. Please deploy the corresponding [NRLF account wide infrastructure](../account-wide-infrastructure/README.md) first.

## Deploy infrastructure

To deploy the infrastructure, you need to build the NRLF artifacts and then deploy them with Terraform.

The steps are as follows:

### Build artifacts for deployment

First, build the NRLF artifacts that will be deployed by Terraform:

```shell
$ make build-artifacts
```

### Init your local workspace

On the first deployment, you will need to initialise and select your workspace. To do this, run:

```shell
$ make init
```

If your Terraform provider config changes, you may need to run `make init` again.

### Create a Terraform plan

To create a Terraform plan:

```shell
$ make plan
```

### Apply the changes with Terraform

To apply your changes:

```shell
$ make apply
```

## Tear down infrastructure

To tear down the infrastructure, you need to use Terraform to destroy the resources in your Terraform workspace.

To do this, follow these steps:

### Init your local workspace

On the first deployment, you will need to initialise and select your workspace. To do this, run:

```shell
$ make init
```

### Teardown infrastructure

To teardown the infrastructure, do the following:

```
$ make destroy
```
