resource "aws_kms_key" "document-pointer" {
  description             = "Document types table KMS key"
  deletion_window_in_days = var.kms_deletion_window_in_days

}

resource "aws_kms_alias" "document-pointer" {
  name          = "alias/${var.name_prefix}--document-pointer"
  target_key_id = aws_kms_key.document-pointer.key_id
}
