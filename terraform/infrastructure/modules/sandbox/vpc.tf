resource "aws_vpc" "sandbox" {
  cidr_block           = var.vpc_cidr_block
  enable_dns_support   = true
  enable_dns_hostnames = true
}

resource "aws_vpc_endpoint" "sandbox-ecs" {
  count               = length(var.vpc_endpoint_services)
  vpc_id              = aws_vpc.sandbox.id
  service_name        = "com.amazonaws.${var.region}.${var.vpc_endpoint_services[count.index]}"
  vpc_endpoint_type   = "Interface"
  security_group_ids  = [aws_security_group.sandbox-ecs.id]
  subnet_ids          = aws_subnet.private.*.id
  private_dns_enabled = true

  depends_on = [
    aws_vpc.sandbox,
    aws_security_group.sandbox-ecs
  ]
}
