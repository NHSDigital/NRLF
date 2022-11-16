# NRLF Account Wide Infrastructure

This directory contains terraform for resources which are global to a given account instead of a workspace. Resources can include but not limited to: User assume IAM roles, Route 53 DNS setup and API gateway cloudwatch roles etc.

Each subdirectory corresponds to each AWS account (`mgmt`, `prod`, `test` and `dev`).

**Account wide resources should be deployed manually and not be run as part of CI.**

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Initialise shell environment](#initialise-shell-environment)
3. [Deploy account wide resources](#deploy-account-wide-resources)
4. [Tear down account wide resources](#tear-down-account-wide-resources)

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

## Deploy account wide resources

Login to `mgmt` account as admin.

```shell
nrlf aws login mgmt-adminyour
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

After confirming the changes from the terraform plan output, apply changes

```shell
nrlf terraform apply <account> account_wide
```

## Tear down account wide resources

Login to `mgmt` account as admin.

```shell
nrlf aws login mgmt-adminyour
```

Initialise terraform

```shell
nrlf terraform init <account> account_wide
```

Tear down

```shell
nrlf terraform destroy <account> account_wide
```
