# NRLF main infrastructure

This directory contains terraform to build the main NRLF api infrastructure.

NRLF project uses terraform workspaces to handle deploying multiple NRLF stacks to each of our environments. NRFL stacks are identified by their TF workspace id. Resources in each stack will contain the workspace id in its name. (e.g. nhsd-nrlf--dev-pointers-table or nhsd-nrlf--469d5da6-pointers-table).

Each developer/QA can create their own ephemeral instance of the NRLF infrastructure. These are deployed as isolated NRLF stacks into the dev AWS account and use variables in `etc/dev.tfvars`.

This project has a number of "persistent environments", similar to traditional dev, ref and prod environments. Each of these environments will typically contain multiple NRLF stacks, allowing for blue/green style deployment, and have shared storage infrastructure like DynamoDB tables and S3 buckets. The persistent environments are deployed as follows:

| Environment  | TF Workspace  | TF Config         | AWS Account | Internal Domain                      | Public Domain                             |
| ------------ | ------------- | ----------------- | ----------- | ------------------------------------ | ----------------------------------------- |
| internal-dev | dev-N         | `etc/dev.tfvars`  | dev         | `record-locator.dev.national.nhs.uk` | `internal-dev.api.service.nhs.uk`         |
| dev-sandbox  | dev-sandbox-N | `etc/dev.tfvars`  | dev         | `record-locator.dev.national.nhs.uk` | `internal-dev-sandbox.api.service.nhs.uk` |
| internal-qa  | qa-N          | `etc/qa.tfvars`   | test        | `qa.record-locator.national.nhs.uk`  | `internal-qa.api.service.nhs.uk`          |
| qa-sandbox   | qa-sandbox-N  | `etc/qa.tfvars`   | test        | `qa.record-locator.national.nhs.uk`  | `internal-qa-sandbox.api.service.nhs.uk`  |
| int          | int-N         | `etc/int.tfvars`  | test        | `record-locator.int.national.nhs.uk` | `int.api.service.nhs.uk`                  |
| sandbox      | int-sandbox-N | `etc/int.tfvars`  | test        | `record-locator.int.national.nhs.uk` | `sandbox.api.service.nhs.uk`              |
| ref          | ref-N         | `etc/ref.tfvars`  | test        | `record-locator.ref.national.nhs.uk` | `ref.api.service.nhs.uk`                  |
| prod         | prod-N        | `etc/prod.tfvars` | prod        | `record-locator.national.nhs.uk`     | `api.service.nhs.uk`                      |

The `N` in the TF workspace name repesents the stack id in that environment. So, for example, the internal-dev environment might have two stacks, `dev-1` and `dev-2` with TF workspace names matching their stack names. All resources for the `dev-1` stack will be contained within the `dev-1` TF workspace.

CI pipeline creates infrastructure in the dev AWS account. These will have workspace id of `nrl<jira-id>-<first six char of commit hash>` and use variables in `etc/dev.tfvars`

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

On the first deployment, you will need to initialise and create your workspace. To create a new ephemeral dev workspace, run:

```shell
$ make init
```

If you want to use an existing workspace, or if you want to use the workspace of a persistent environment, do the following:

```shell
$ make ENV={ENV_NAME} TF_WORKSPACE_NAME={WORKSPACE_NAME} init
```

replacing `{ENV_NAME}` with the environment name (e.g. `dev`, `qa`, `qa-sandbox` etc) and `{WORKSPACE_NAME}` with the name of the workspace/stack you want to use.

So, for example, if you want to use the `qa` environment and deploy to the `qa-1` stack, you'd do the following:

```shell
$ make ENV=qa TF_WORKSPACE_NAME=qa-1 init
```

If your Terraform provider config changes, you may need to reinitialise your workspace.

### Create a Terraform plan

To create a Terraform plan for a dev workspace:

```shell
$ make plan
```

To create a Terraform plan for a workspace in another environment:

```shell
$ make ENV={ENV_NAME} plan
```

replacing `{ENV_NAME}` with the environment name (e.g. `dev`, `qa`, `qa-sandbox` etc).

### Apply the changes with Terraform

To apply your changes to a dev workspace:

```shell
$ make apply
```

To apply your changes to a workspace in another environment:

```shell
$ make ENV={ENV_NAME} apply
```

replacing `{ENV_NAME}` with the environment name (e.g. `dev`, `qa`, `qa-sandbox` etc).

## Tear down infrastructure

To tear down the infrastructure, you need to use Terraform to destroy the resources in your Terraform workspace.

To teardown the infrastructure, do the following:

```
$ make ENV={ENV_NAME} TF_WORKSPACE_NAME={WORKSPACE_NAME} init destroy
```

replacing `{ENV_NAME}` with the environment name (e.g. `dev`, `qa`, `qa-sandbox` etc) and `{WORKSPACE_NAME}` with the name of the workspace/stack you want to destroy.
