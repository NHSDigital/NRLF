provider "aws" {
  region = var.region_name
  assume_role {
    role_arn = "arn:aws:iam::${var.assume_account}:role/${var.assume_role}"
  }

  default_tags {
    tags = {
      project_name = var.project_name
      workspace    = terraform.workspace
    }
  }

}

terraform {
  backend "s3" {
    encrypt              = false
    region               = "eu-west-2"
    bucket               = "nhsd-nrlf-terraform-state"
    dynamodb_table       = "nhsd-nrlf-terraform-state-lock"
    key                  = "terraform-state"
    workspace_key_prefix = "nhsd-nrlf"
  }
}
