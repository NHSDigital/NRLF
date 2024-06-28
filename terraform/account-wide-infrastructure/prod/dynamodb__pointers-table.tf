module "prod-pointers-table" {
  source                      = "../modules/pointers-table"
  name_prefix                 = "nhsd-nrlf--prod"
  enable_deletion_protection  = true
  enable_pitr                 = true
  kms_deletion_window_in_days = 30
}
