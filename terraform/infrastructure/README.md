# NRLF main infrastructure

This directory contains terraform to build the main NRLF api infrastructure.

NRLF project uses terraform workspaces to handle multiple "environments". Environments are identified by their workspace id. Resources in each environment will contain workspace id in its name. (e.g. nhsd-nrlf--dev--document-pointer or nhsd-nrlf--469d5da6--document-pointer)

Each developer/QA can create their own instance of NRLF infrastructure. These are deployed to the dev AWS account and use variables in `etc/dev.tfvars`

This project also use three "persistent environments". These are equivalent to traditional dev, ref and prod environments. The persistent environments are deployed to the following AWS accounts:

- `prod` environment is deployed to prod AWS account with variables in `etc/prod.tfvars`
- `ref` environment is deployed to test AWS account with variables in `etc/test.tfvars`
- `int` environment is deployed to test AWS account with variables in `etc/uat.tfvars`
- `dev` environment is deployed to dev AWS account with variables in `etc/dev.tfvars`

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

To deploy the infrastructure, you need to build the NRLF artifacts and then deployment them with Terraform.

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
