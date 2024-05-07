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

Before deploying the NRLF account-wide infrastructure, you will need:

- AWS accounts that have already been bootstrapped, as described in [bootstrap/README.md](../bootstrap/README.md). This is a one-time account setup step.
- The required packages to build NRLF, see [the Setup section in README.md](../../README.md#setup).

## Deploy account wide resources

To deploy the account wide resources, first login to the AWS mgmt account on the CLI.

Then, initialise your terraform workspace with:

```shell
$ cd ACCOUNT_NAME
$ terraform init && ( \
    terraform workspace new ACCOUNT_NAME || \
    terraform workspace select ACCOUNT_NAME )
```

Replacing ACCOUNT_NAME with the name of your account, e.g `dev`, `test` etc.

Once you have your workspace, you can plan your changes with:

```shell
$ terraform plan \
    -var 'assume_account=AWS_ACCOUNT_ID' \
    -var 'assume_role=terraform'
```

Replacing AWS_ACCOUNT_ID with the AWS account number of your account.

Once you're happy with your planned changes, you can apply them with:

```shell
$ terraform apply \
    -var 'assume_account=AWS_ACCOUNT_ID' \
    -var 'assume_role=terraform'
```

Replacing AWS_ACCOUNT_ID with the AWS account number of your account.

## Tear down account wide resources

WARNING - This action will destroy all account-wide resources from the AWS account. This should
only be done if you are sure that this is safe and are sure that you are signed into the correct
AWS account.

To tear down account-wide resources, first login to the AWS mgmt account on the CLI.

Then, initialise your terraform workspace with:

```shell
$ cd ACCOUNT_NAME
$ terraform init && ( \
    terraform workspace new account_wide || \
    terraform workspace select account_wide )
```

And then, to tear down:

```shell
$ terraform destroy \
    -var 'assume_account=AWS_ACCOUNT_ID' \
    -var 'assume_role=terraform'
```
