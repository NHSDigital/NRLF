module "prod-permissions-store-bucket" {
  source      = "../modules/permissions-store-bucket"
  name_prefix = "nhsd-nrlf--prod"
}

module "prod-truststore-bucket" {
  source                  = "../modules/truststore-bucket"
  name_prefix             = "nhsd-nrlf--prod"
  server_certificate_file = "../../../truststore/server/prod.pem"
}
