resource "aws_dynamodb_table" "dynamodb_terraform_state_lock" {
  name           = "${var.project_name}-terraform-state-lock"
  hash_key       = "LockID"
  read_capacity  = 20
  write_capacity = 20

  attribute {
    name = "LockID"
    type = "S"
  }
}
