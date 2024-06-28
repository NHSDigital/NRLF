module "qa-permissions-store-bucket" {
  source      = "../modules/permissions-store-bucket"
  name_prefix = "nhsd-nrlf--qa"
}

module "qa-sandbox-permissions-store-bucket" {
  source      = "../modules/permissions-store-bucket"
  name_prefix = "nhsd-nrlf--qa-sandbox"
}

module "int-permissions-store-bucket" {
  source      = "../modules/permissions-store-bucket"
  name_prefix = "nhsd-nrlf--int"
}

module "int-sandbox-permissions-store-bucket" {
  source      = "../modules/permissions-store-bucket"
  name_prefix = "nhsd-nrlf--int-sandbox"
}

module "ref-permissions-store-bucket" {
  source      = "../modules/permissions-store-bucket"
  name_prefix = "nhsd-nrlf--ref"
}

module "qa-truststore-bucket" {
  source                  = "../modules/truststore-bucket"
  name_prefix             = "nhsd-nrlf--qa"
  server_certificate_file = "../../../truststore/server/qa.pem"
}

module "qa-sandbox-truststore-bucket" {
  source                  = "../modules/truststore-bucket"
  name_prefix             = "nhsd-nrlf--qa-sandbox"
  server_certificate_file = "../../../truststore/server/qa.pem"
}

module "int-truststore-bucket" {
  source                  = "../modules/truststore-bucket"
  name_prefix             = "nhsd-nrlf--int"
  server_certificate_file = "../../../truststore/server/int.pem"
}

module "int-sandbox-truststore-bucket" {
  source                  = "../modules/truststore-bucket"
  name_prefix             = "nhsd-nrlf--int-sandbox"
  server_certificate_file = "../../../truststore/server/int.pem"
}

module "ref-truststore-bucket" {
  source                  = "../modules/truststore-bucket"
  name_prefix             = "nhsd-nrlf--ref"
  server_certificate_file = "../../../truststore/server/ref.pem"
}
