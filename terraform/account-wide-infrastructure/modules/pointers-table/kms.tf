resource "aws_kms_key" "pointers-table-key" {
  description             = "Document pointers table KMS key"
  deletion_window_in_days = var.kms_deletion_window_in_days

}

resource "aws_kms_alias" "pointers-table-alias" {
  name          = "alias/${var.name_prefix}-pointers-table-key"
  target_key_id = aws_kms_key.pointers-table-key.key_id
}
