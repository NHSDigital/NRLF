resource "aws_db_instance" "rds" {
  identifier          = "${replace(var.prefix, "--", "-")}-${var.name}-rds"
  instance_class      = var.rds_instance_class
  username            = "nrlfadmin"
  password            = random_password.rds_password.result
  publicly_accessible = true
  skip_final_snapshot = true
  allocated_storage   = var.rds_allocated_storage
  engine              = "postgres"
  engine_version      = "14.1"

  db_subnet_group_name   = aws_db_subnet_group.rds.name
  vpc_security_group_ids = [aws_security_group.rds.id]
  parameter_group_name   = aws_db_parameter_group.rds.name

}

resource "aws_db_parameter_group" "rds" {
  name   = "rds"
  family = "postgres14"

  parameter {
    name  = "log_connections"
    value = "1"
  }
}
