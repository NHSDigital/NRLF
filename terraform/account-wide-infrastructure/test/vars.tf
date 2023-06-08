variable "assume_account" {
  sensitive = true
}

variable "assume_role" {}

variable "private_subnet_cidr_blocks" {
  description = "Available CIDR blocks for private subnets"
  type        = list(string)
  default = [
    "10.0.1.0/24",
    "10.0.2.0/24",
    "10.0.3.0/24",
    "10.0.4.0/24",
  ]
}

variable "subnet_count" {
  description = "Number of subnets"
  type        = map(number)
  default = {
    private = 3
  }
}

variable "vpc_cidr_block" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "engine_version" {
  description = "engine version for rds cluster"
  type        = string
  default     = "15.2"
}

variable "engine" {
  description = "enginer for the rds cluster"
  type        = string
  default     = "aurora-postgresql"
}

variable "user_name" {
  description = "user name for the database cluster"
  type        = string
  default     = "nrlf"
}

variable "instance_type" {
  description = "Instance type for the database instance"
  type        = string
  default     = "db.t3.medium"
}
