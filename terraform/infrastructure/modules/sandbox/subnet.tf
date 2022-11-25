resource "aws_subnet" "public" {
  count                   = length(var.availability_zones)
  vpc_id                  = aws_vpc.sandbox.id
  cidr_block              = cidrsubnet(var.vpc_cidr_block, var.newbits, count.index)
  availability_zone       = element(var.availability_zones, count.index)
  map_public_ip_on_launch = true

  tags = {
    Name = "${var.prefix}--public-sandbox--${count.index}"
  }

  depends_on = [
    aws_vpc.sandbox
  ]
}

resource "aws_subnet" "private" {
  count                   = length(var.availability_zones)
  vpc_id                  = aws_vpc.sandbox.id
  cidr_block              = cidrsubnet(var.vpc_cidr_block, var.newbits, count.index + length(var.availability_zones) + 1)
  availability_zone       = element(var.availability_zones, count.index)
  map_public_ip_on_launch = false


  tags = {
    Name = "${var.prefix}--private-sandbox--${count.index}"
  }


  depends_on = [
    aws_vpc.sandbox
  ]
}
