resource "aws_iam_instance_profile" "sandbox" {
  name = "${var.prefix}--ec2-instance-profile--sandbox"
  role = aws_iam_role.ecs_agent.name
}

resource "aws_launch_configuration" "sandbox" {
  name_prefix          = "${var.prefix}--sandbox"
  image_id             = "ami-06917a592e3e2d4c6"
  iam_instance_profile = aws_iam_instance_profile.sandbox.name
  security_groups      = [aws_security_group.sandbox-ecs.id]
  user_data            = <<EOF
  #!/bin/bash
  echo ECS_CLUSTER=${aws_ecs_cluster.sandbox.name} >> /etc/ecs/ecs.config
  echo ECS_AVAILABLE_LOGGING_DRIVERS='["json-file","awslogs"]' >> /etc/ecs/ecs.config"
  EOF

  instance_type = var.instance_type

  lifecycle {
    create_before_destroy = true
  }
}


resource "aws_autoscaling_group" "sandbox" {
  name                      = "${var.prefix}--ec2-autoscaling--sandbox"
  vpc_zone_identifier       = aws_subnet.private.*.id
  launch_configuration      = aws_launch_configuration.sandbox.name
  desired_capacity          = 1
  min_size                  = 1
  max_size                  = 1
  health_check_grace_period = 300
  health_check_type         = "EC2"

  lifecycle {
    create_before_destroy = true
  }
}
