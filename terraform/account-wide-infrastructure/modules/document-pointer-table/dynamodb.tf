resource "aws_dynamodb_table" "document-pointer" {
  name                        = "${var.name_prefix}--document-pointer"
  billing_mode                = "PAY_PER_REQUEST"
  hash_key                    = "pk"
  range_key                   = "sk"
  deletion_protection_enabled = var.enable_deletion_protection

  attribute {
    name = "pk"
    type = "S"
  }

  attribute {
    name = "sk"
    type = "S"
  }

  attribute {
    name = "patient_key"
    type = "S"
  }

  attribute {
    name = "patient_sort"
    type = "S"
  }

  attribute {
    name = "masterid_key"
    type = "S"
  }

  global_secondary_index {
    name            = "patient_gsi"
    hash_key        = "patient_key"
    range_key       = "patient_sort"
    projection_type = "ALL"
  }

  global_secondary_index {
    name            = "masterid_gsi"
    hash_key        = "masterid_key"
    projection_type = "ALL"
  }

  server_side_encryption {
    enabled     = true
    kms_key_arn = aws_kms_key.document-pointer.arn
  }

  point_in_time_recovery {
    enabled = var.enable_pitr
  }
}
