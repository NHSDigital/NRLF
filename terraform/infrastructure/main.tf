provider "aws" {
  region = local.region
  # assume_role {
  #   role_arn = "arn:aws:iam::${var.assume_account}:role/${var.assume_role}"
  # }

  default_tags {
    tags = {
      project_name = local.project
      workspace    = terraform.workspace
    }
  }
}

terraform {
  backend "s3" {
    encrypt              = false
    region               = "eu-west-2"
    bucket               = "nhsd-nrlf--terraform-state"
    dynamodb_table       = "nhsd-nrlf--terraform-state-lock"
    key                  = "terraform-state-infrastructure"
    workspace_key_prefix = "nhsd-nrlf"
  }

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }

    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
  }
}
