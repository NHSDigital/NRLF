resource "aws_eip" "sandbox" {
  count = length(aws_subnet.public)
  vpc   = true

  depends_on = [
    aws_subnet.public
  ]
}
