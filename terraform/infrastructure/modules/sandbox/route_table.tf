resource "aws_route_table" "public" {
  vpc_id = aws_vpc.sandbox.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.sandbox.id
  }
  tags = {
    Name = "${var.prefix}--public-route-table--sandbox"
  }

  depends_on = [
    aws_vpc.sandbox,
    aws_internet_gateway.sandbox
  ]
}

resource "aws_route_table" "private" {
  count  = length(aws_subnet.private)
  vpc_id = aws_vpc.sandbox.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.sandbox[count.index].id
  }
  tags = {
    Name = "${var.prefix}--private-route-table--sandbox"
  }

  depends_on = [
    aws_vpc.sandbox,
  ]
}

resource "aws_route_table_association" "public" {
  count          = length(aws_subnet.public)
  route_table_id = aws_route_table.public.id
  subnet_id      = element(aws_subnet.public.*.id, count.index)

  depends_on = [
    aws_subnet.public,
    aws_route_table.public
  ]
}

resource "aws_route_table_association" "private" {
  count          = length(aws_subnet.private)
  route_table_id = element(aws_route_table.private.*.id, count.index)
  subnet_id      = element(aws_subnet.private.*.id, count.index)

  depends_on = [
    aws_subnet.private,
    aws_route_table.private
  ]
}
