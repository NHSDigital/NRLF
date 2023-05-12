output "rds_hostname" {
  description = "RDS instance hostname"
  value       = aws_db_instance.rds.address
  sensitive   = true
}

output "rds_port" {
  description = "RDS instance port"
  value       = aws_db_instance.rds.port
  sensitive   = true
}

output "rds_username" {
  description = "RDS instance root username"
  value       = aws_db_instance.rds.username
  sensitive   = true
}

output "rds_password" {
  description = "RDS instance password"
  value       = random_password.rds_password.result
  sensitive   = true
}
