variable "prefix" {}

variable "name" {}

variable "db_instance_class" {
  type    = string
  default = "db.t3.micro"
}

variable "db_allocated_storage" {
  type    = string
  default = 5
}
