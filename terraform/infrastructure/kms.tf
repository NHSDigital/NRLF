locals {
  kms = {
    deletion_window_in_days = var.deletion_window_in_days
  }
}

variable "deletion_window_in_days" {
  type    = number
  default = 7
}

data "aws_iam_policy_document" "kms_default_policy" {
  statement {
    principals {
      type = "AWS"

      identifiers = [
        "arn:aws:iam::${var.assume_account}:root",
      ]
    }

    actions = [
      "kms:*",
    ]

    resources = [
      "*"
    ]

    sid = "Enable IAM User Permissions"
  }
}
