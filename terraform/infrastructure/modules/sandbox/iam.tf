#--- ECS agent, operating inside EC2
data "aws_iam_policy_document" "ecs_agent" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
  }
}
resource "aws_iam_role" "ecs_agent" {
  name               = "${var.prefix}--ecs-agent-role-sandbox"
  assume_role_policy = data.aws_iam_policy_document.ecs_agent.json
}

resource "aws_iam_role_policy_attachment" "ecs_agent" {
  role       = aws_iam_role.ecs_agent.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonEC2ContainerServiceforEC2Role"
}

#--- ECS task, executing EC2
data "aws_iam_policy_document" "ecs_task" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }

}

resource "aws_iam_role" "ecs_task" {
  name               = "${var.prefix}--ecs-task-role--sandbox"
  assume_role_policy = data.aws_iam_policy_document.ecs_task.json
}


#--- ECS task, cloudwatch logs

data "aws_iam_policy_document" "ecs_cloudwatch" {
  statement {
    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents",
      "logs:CreateLogGroup"
    ]
    effect    = "Allow"
    resources = ["*"]
  }
}

resource "aws_iam_policy" "ecs_cloudwatch" {
  name   = "${var.prefix}--ecs-cloudwatch--sandbox"
  policy = data.aws_iam_policy_document.ecs_cloudwatch.json
}

resource "aws_iam_role_policy_attachment" "ecs_cloudwatch" {
  role       = aws_iam_role.ecs_task.name
  policy_arn = aws_iam_policy.ecs_cloudwatch.arn
  depends_on = [
    aws_iam_role.ecs_task
  ]
}

#--- ECS task, execution role

resource "aws_iam_role_policy_attachment" "ecs_execution" {
  role       = aws_iam_role.ecs_task.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
  depends_on = [
    aws_iam_role.ecs_task
  ]
}
