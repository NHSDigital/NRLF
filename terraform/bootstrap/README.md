# NRLF AWS Account Initial Bootstrap

This directory contains files needed for initial setup for brand new AWS accounts. Directory is split in to two sub directories. `mgmt` directory contains files required for initial bootstrap of the `mgmt` account. `non-mgmt` directory contains files required for initial bootstrap of `prod`, `test` and `dev` accounts.

The setup creates AWS resources to enable the `nrlf.sh` shell script to be run and enable terraform deployments to AWS accounts. This should only be required to be performed once.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Initialise shell environment](#initialise-shell-environment)
3. [Running initial project setup](#running-initial-project-setup)
   1. [Setup mgmt account resources](#1-setup-mgmt-account-resources)
   2. [Create trust role for non mgmt accounts](#2-create-trust-role-for-mgmt-for-your-prod-test-and-dev-accounts)
4. [Tearing down setup](#tearing-down-setup)
   1. [Tear down mgmt account resources](#1-tear-down-mgmt-account-resources)
   2. [Tear down non mgmt account resources](#2-tear-down-prod-test-and-dev-account-resources)

## Prerequisites

- Four AWS accounts created. These will be assigned as: mgmt, prod, test and dev
- Required packages installed to enable running of `nrlf.sh` shell script see [Setup](../../README.md#setup)

## Initialise shell environment

To use `nrlf` shell script commands. We must initialise the shell environment. Ensure all packages are installed, run the following commands at the root of the repository.

```shell
poetry shell
source nrlf.sh
```

This will enable the `nrlf` commands.

## Running initial project setup

Before performing initial setup, ensure you have [initialised the shell environment](#initialise-shell-environment).

**These steps should only need to be run once when starting the project**

### 1. Setup mgmt account resources

This will set up your terraform state buckets and import them into your project.

Login to `mgmt` account:

```shell
nrlf aws login mgmt-admin
```

Create resources on mgmt account required for terraform to work. This includes:

- terraform state bucket
- terraform state lock table
- secret managers to hold account ids for the non-mgmt accounts

```shell
nrlf bootstrap create-mgmt
```

Now log on to AWS web console and manually add the aws account ids to each respective secrets
`nhsd-nrlf--mgmt--mgmt-account-id`, `nhsd-nrlf--mgmt--prod-account-id`, `nhsd-nrlf--mgmt--test-account-id` and `nhsd-nrlf--mgmt--dev-account-id`

### 2. Create trust role for `mgmt` for your `prod`, `test` and `dev` accounts

In order to allow `mgmt` to create resources in `prod`, `test` and `dev` accounts you
need to create a trust role in each of these accounts.

Log in to your non-mgmt account (e.g. `dev`):

```shell
nrlf aws login <non-mgmt-account>-admin
```

Create the trust role:

```shell
nrlf bootstrap create-non-mgmt
```

## Tearing down setup

When closing AWS accounts, resources created by this setup will need to be torn down.

Before performing the teardown, ensure you have [initialised the shell environment](#initialise-shell-environment).

### 1. Tear down mgmt account resources

This will tear down resources created in this [step](#1-setup-mgmt-account-resources)

Log in to your `mgmt` account:

```shell
nrlf aws login mgmt-admin
```

Run tear down script

```shell
nrlf bootstrap delete-mgmt
```

### 2. Tear down `prod`, `test` and `dev` account resources

This will tear down resources created in this [step](#2-create-trust-role-for-mgmt-for-your-prod-test-and-dev-accounts)

Log in to your non-mgmt account (e.g. `dev`):

```shell
nrlf aws login <non-mgmt-account>-admin
```

Run tear down script

```shell
nrlf bootstrap delete-non-mgmt
```
