module "qa-document-pointer-table" {
  source                     = "../modules/document-pointer-table"
  name_prefix                = "nhsd-nrlf--qa"
  enable_deletion_protection = true
}

module "qa-sandbox-document-pointer-table" {
  source      = "../modules/document-pointer-table"
  name_prefix = "nhsd-nrlf--qa-sandbox"
}

module "int-document-pointer-table" {
  source                      = "../modules/document-pointer-table"
  name_prefix                 = "nhsd-nrlf--int"
  enable_deletion_protection  = true
  enable_pitr                 = true
  kms_deletion_window_in_days = 30
}

module "int-sandbox-document-pointer-table" {
  source      = "../modules/document-pointer-table"
  name_prefix = "nhsd-nrlf--int-sandbox"
}

module "ref-document-pointer-table" {
  source                      = "../modules/document-pointer-table"
  name_prefix                 = "nhsd-nrlf--ref"
  enable_deletion_protection  = true
  enable_pitr                 = true
  kms_deletion_window_in_days = 30
}
