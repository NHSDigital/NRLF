module "dev-pointers-table" {
  source      = "../modules/pointers-table"
  name_prefix = "nhsd-nrlf--dev"
}

module "dev-sandbox-pointers-table" {
  source      = "../modules/pointers-table"
  name_prefix = "nhsd-nrlf--dev-sandbox"
}
