variable "region" {}
variable "prefix" {}
variable "project" {}
variable "environment" {}
variable "availability_zones" {}
variable "vpc_cidr_block" {}
variable "n_cpus" {}
variable "memory" {}
variable "instance_type" {}
variable "newbits" {
  default = 8
}

variable "vpc_endpoint_services" {
  default = ["ecs-agent", "ecs-telemetry", "ecs"]
}
variable "container_name" {
  default = "localstack_main"
}
variable "proxy_port" {
  default = 8000
}
variable "localstack_port" {
  default = 4566
}
