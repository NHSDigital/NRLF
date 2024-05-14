# NRLF AWS Account Initial Bootstrap

This directory contains files needed for initial setup for brand new AWS accounts. Directory is split in to two sub directories. `mgmt` directory contains files required for initial bootstrap of the `mgmt` account. `non-mgmt` directory contains files required for initial bootstrap of `prod`, `test` and `dev` accounts.

The setup creates AWS resources to enable terraform deployments to AWS accounts. This should only be required to be performed once.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Bootstrapping the environments](#bootstrapping-the-environments)
3. [Tearing down the environments](#tearing-down-the-environments)

## Prerequisites

Before you begin deploying NRLF bootstrap components, you will need:

- Four AWS accounts created. These will be assigned as: mgmt, prod, test and dev
- The required packages to build NRLF, see [the Setup section in README.md](../../README.md#setup).

## Bootstrapping the environments

To bootstrap the environments, you need to follow these steps.

**These steps should only need to be run once when starting the project**

### Setup mgmt account resources

This will set up your terraform state buckets and import them into your project. It
will create resources on mgmt account required for terraform to work. This includes:

- terraform state bucket
- terraform state lock table
- secret managers to hold account ids for the non-mgmt accounts

To create these resource, first login to the AWS mgmt account on your CLI and then run:

```shell
./scripts/bootstrap.sh create-mgmt
```

Now log on to AWS web console and manually add the aws account ids to each respective secrets:

- `nhsd-nrlf--mgmt--mgmt-account-id`
- `nhsd-nrlf--mgmt--prod-account-id`
- `nhsd-nrlf--mgmt--test-account-id`
- `nhsd-nrlf--mgmt--dev-account-id`

### Create trust role for `mgmt` for your `prod`, `test` and `dev` accounts

In order to allow `mgmt` to create resources in `prod`, `test` and `dev` accounts you
need to create a trust role in each of these accounts.

To create this role, first login to your non-mgmt account on your CLI and then run:

```shell
./scripts/bootstrap.sh create-non-mgmt
```

## Tearing down the environments

When closing AWS accounts, resources created by this setup will need to be torn down.

### Tear down `prod`, `test` and `dev` account resources

This will tear down resources created in this [step](#create-trust-role-for-mgmt-for-your-prod-test-and-dev-accounts)

To tear down the non-mgmt account, first login to that non-mgmt AWS account on your CLI and then run:

```shell
./scripts/bootstrap.sh delete-non-mgmt
```

### Tear down mgmt account resources

This will tear down resources created in this [step](#setup-mgmt-account-resources).

To tear down management resource, first login to the AWS mgmt account on your CLI and then run:

```shell
./scripts/bootstrap.sh delete-mgmt
```
