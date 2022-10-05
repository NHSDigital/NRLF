# NRLF

## Prerequisites

- pipenv
- python 3.9
- terraform
- jq
- tfenv

## Install python dependencies

```
pipenv install --dev
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

## Project bootstrap

### Create Terraform state files

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

Create and import state buckets:

```
nrlf bootstrap create-mgmt-state
```

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
nrlf bootstrap create-terraform-role-non-mgmt
```

## Create / update account-wide resources for non-`mgmt` accounts

Whenever you need to update account-wide resources for non-`mgmt` accounts (e.g. `dev`, `prod`, `test`).
This is for resources such as Cloudwatch roles which are global to a given account.

Log in to your `mgmt` account.

```
nrlf aws login mgmt-admin
```

Update account wide resources for non-`mgmt` accounts (e.g. `dev`):

```
nrlf terraform bootstrap-non-mgmt <non-mgmt-account>
```
