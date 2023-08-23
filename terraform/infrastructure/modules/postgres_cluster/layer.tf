module "psycopg2" {
  source = "../layer"
  name   = "psycopg2"
  prefix = var.prefix
}

module "nrlf" {
  source = "../layer"
  name   = "nrlf"
  prefix = var.prefix
}

module "lambda_utils" {
  source = "../layer"
  name   = "lambda_utils"
  prefix = var.prefix
}
