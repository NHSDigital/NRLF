module "ephemeral-resources" {
    count  = local.use_shared_resources ? 0 : 1
    source = "./modules/ephemeral-resources"
    prefix = local.prefix
}
