resource "aws_internet_gateway" "sandbox" {
  vpc_id = aws_vpc.sandbox.id
}

resource "aws_nat_gateway" "sandbox" {
  count         = length(aws_subnet.public)
  allocation_id = aws_eip.sandbox[count.index].id
  subnet_id     = aws_subnet.public[count.index].id

  depends_on = [
    aws_vpc.sandbox,
    aws_subnet.public,
    aws_eip.sandbox
  ]
}
