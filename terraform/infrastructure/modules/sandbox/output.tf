output "sandbox_image_name" {
  value = aws_ecr_repository.sandbox.name
}

output "sandbox_ecs_cluster" {
  value = {
    cluster = aws_ecs_cluster.sandbox.name
    service = aws_ecs_service.sandbox.name
  }
}
