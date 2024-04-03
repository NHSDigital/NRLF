module "nrlf" {
  source = "./modules/layer"
  name   = "nrlf"
  prefix = local.prefix
}

module "third_party" {
  source = "./modules/layer"
  name   = "dependency_layer"
  prefix = local.prefix
}

module "fhirguard_metadata" {
  source = "./modules/layer"
  name   = "fhirguard-metadata"
  prefix = local.prefix
}
