resource "aws_instance" "bastion" {
  count                       = var.environment == "prod" ? 0 : 1
  ami                         = "ami-00785f4835c6acf64"
  instance_type               = "t3.micro"
  subnet_id                   = element(aws_subnet.public_subnet, count.index).id
  vpc_security_group_ids      = [aws_security_group.bastion.id]
  associate_public_ip_address = true
  key_name                    = data.aws_key_pair.bastion_key[0].key_name
  user_data                   = <<EOF
      #!/bin/bash
      echo "Installing psql client"
      sudo yum install postgresql.x86_64
      echo "Finished installing psql"
    EOF

  tags = {
    "Name" = "bastion-${var.environment}"
  }
}


data "aws_key_pair" "bastion_key" {
  count              = var.environment == "prod" || length(regexall("--ci-", var.environment)) > 0 ? 0 : 1
  key_name           = "${var.environment}-bastion-key"
  include_public_key = true
}
