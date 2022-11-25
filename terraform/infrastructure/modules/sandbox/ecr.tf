resource "aws_ecr_repository" "sandbox" {
  name = "${var.project}-${var.environment}-ecr-sandbox"
}
