# NRLF main infrastructure

This directory contains terraform to build the main NRLF api infrastructure.

NRLF project uses terraform workspaces to handle multiple "environments". Environments are identified by their workspace id. Resources in each environment will contain workspace id in its name. (e.g. nhsd-nrlf--dev--document-pointer or nhsd-nrlf--469d5da6--document-pointer)

Each developer/QA can create their own instance of NRLF infrastructure. These are deployed to the dev AWS account and use variables in `etc/dev.tfvars`

This project also use three "persistent environments". These are equivalent to traditional dev, ref and prod environments. The persistent environments are deployed to the following AWS accounts:

- `prod` environment is deployed to prod AWS account with variables in `etc/prod.tfvars`
- `ref` environment is deployed to test AWS account with variables in `etc/test.tfvars`
- `dev` environment is deployed to dev AWS account with variables in `etc/dev.tfvars`

CI pipeline creates infrastructure in the test AWS account. These will have workspace id of `<first six char of commit hash>-ci` and use variables in `etc/test.tfvars`

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Initialise shell environment](#initialise-shell-environment)
3. [Deploy infrastructure](#deploy-infrastructure)
   1. [Build artifacts](#1-build-artifacts-for-deployment)
   2. [Login to AWS](#2-login-to-aws-for-deployment)
   3. [Initialise terraform](#3-initialise-terraform-for-deployment)
   4. [Create a terraform plan](#4-create-a-terraform-plan)
   5. [Apply terraform plan](#5-apply-terraform-plan)
4. [Tear down infrastructure](#tear-down-infrastructure)
   1. [Build artifacts](#1-build-artifacts-for-teardown)
   2. [Login to AWS](#2-login-to-aws-for-teardown)
   3. [Initialise terraform](#3-initialise-terraform-for-teardown)
   4. [Teardown infrastructure](#4-teardown-infrastructure)

## Prerequisites

- Initial AWS account [bootstrap](../bootstrap/README.md) completed
- Required packages installed to enable running of `nrlf.sh` shell script see [Setup](../../README.md#setup)

## Initialise shell environment

To use `nrlf` shell script commands. We must initialise the shell environment. Ensure all packages are installed, run the following commands at the root of the repository.

```shell
poetry shell
source nrlf.sh
```

This will enable the `nrlf` commands.

## Deploy infrastructure

Before performing deployment, ensure you have [initialised the shell environment](#initialise-shell-environment).

If infrastructure changes require account wide AWS resources. Please deploy the corresponding [NRLF account wide infrastructure](../account-wide-infrastructure/README.md) first.

### 1. Build artifacts for deployment

To build the artifacts that will be used by terraform.

```
nrlf make build
```

### 2. Login to AWS for deployment

For normal development, login to the normal `mgmt` role. This role can only deploy to dev AWS account which stops accidental deployments to test or prod AWS accounts.

```shell
nrlf aws login mgmt <mfa code>
```

If manual deployments to test or prod AWS accounts are required. Login with `mgmt-admin` role instead.

```shell
nrlf aws login mgmt-admin <mfa code>
```

### 3. Initialise terraform for deployment

```shell
nrlf terraform init
```

### 4. Create a terraform plan

To create a terraform plan for your own workspace (Default workspace id will be the hash of your computer's username).

```shell
nrlf terraform plan
```

Alternatively, to create a plan to a specific workspace, pass in a workspace id.

```shell
nrlf terraform plan <workspace id>
```

### 5. Apply terraform plan

To deploy the terraform plan for your own workspace (Default workspace id will be the hash of your computer's username).

```shell
nrlf terraform apply
```

Alternatively, to deploy to a specific workspace, pass in a workspace id.

```shell
nrlf terraform apply <workspace id>
```

## Tear down infrastructure

Before performing teardown, ensure you have [initialised the shell environment](#initialise-shell-environment).

### 1. Build artifacts for teardown

To build the artifacts that will be used by terraform.

```
nrlf make build
```

### 2. Login to AWS for teardown

For normal development, login to the normal `mgmt` role. This role can only teardown infrastructure deployed in dev AWS account.

```shell
nrlf aws login mgmt <mfa code>
```

If manual teardown to test or prod AWS accounts are required. Login with `mgmt-admin` role instead.

```shell
nrlf aws login mgmt-admin <mfa code>
```

### 3. Initialise terraform for teardown

```shell
nrlf terraform init
```

### 4. Teardown infrastructure

To deploy your own infrastructure (Default workspace id will be the hash of your computer's username).

```shell
nrlf terraform destroy
```

Alternatively, to destroy a specific workspace infrastructure, pass in a workspace id.

```shell
nrlf terraform destroy <workspace id>
```
