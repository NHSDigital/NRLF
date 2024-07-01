module "qa-pointers-table" {
  source                     = "../modules/pointers-table"
  name_prefix                = "nhsd-nrlf--qa"
  enable_deletion_protection = true
}

module "qa-sandbox-pointers-table" {
  source      = "../modules/pointers-table"
  name_prefix = "nhsd-nrlf--qa-sandbox"
}

module "int-pointers-table" {
  source                      = "../modules/pointers-table"
  name_prefix                 = "nhsd-nrlf--int"
  enable_deletion_protection  = true
  enable_pitr                 = true
  kms_deletion_window_in_days = 30
}

module "int-sandbox-pointers-table" {
  source      = "../modules/pointers-table"
  name_prefix = "nhsd-nrlf--int-sandbox"
}

module "ref-pointers-table" {
  source                      = "../modules/pointers-table"
  name_prefix                 = "nhsd-nrlf--ref"
  enable_deletion_protection  = true
  enable_pitr                 = true
  kms_deletion_window_in_days = 30
}
