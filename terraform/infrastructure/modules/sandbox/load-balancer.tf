resource "aws_lb" "sandbox" {
  name               = "${var.prefix}-lb-sbx" # less than 32 chars
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.sandbox-load-balancer.id]
  subnets            = aws_subnet.public.*.id
  idle_timeout       = 300

  depends_on = [
    aws_security_group.sandbox-load-balancer
  ]
}

resource "aws_alb_target_group" "sandbox" {
  name        = "${var.prefix}-ecs-tg"
  port        = 8000
  protocol    = "HTTP"
  vpc_id      = aws_vpc.sandbox.id
  target_type = "ip"

  health_check {
    path                = "/_status"
    port                = 8000
    interval            = 300
    timeout             = 30
    healthy_threshold   = 3
    unhealthy_threshold = 3
  }

  depends_on = [
    aws_lb.sandbox,
    aws_vpc.sandbox
  ]
}

resource "aws_lb_listener" "sandbox" {
  load_balancer_arn = aws_lb.sandbox.arn
  port              = "80"
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_alb_target_group.sandbox.arn
  }

}
