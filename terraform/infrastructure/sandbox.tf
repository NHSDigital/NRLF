module "sandbox" {
  source             = "./modules/sandbox"
  availability_zones = ["eu-west-2a", "eu-west-2b"]
  vpc_cidr_block     = "10.0.0.0/16"
  instance_type      = "t3.small"
  memory             = 4096
  n_cpus             = 2
  region             = local.region
  prefix             = local.prefix
  project            = local.project
  environment        = local.environment
}

output "sandbox_image_name" {
  value = module.sandbox.sandbox_image_name
}

output "sandbox_ecs_cluster" {
  value = module.sandbox.sandbox_ecs_cluster
}
