resource "aws_ecs_cluster" "sandbox" {
  name = "${var.prefix}--ecs-cluster--sandbox"
}

resource "aws_ecs_task_definition" "sandbox" {
  family                   = "${var.prefix}--task-definition--sandbox"
  container_definitions    = <<DEFINITION
  [
    {
      "name": "${var.container_name}",
      "image": "${aws_ecr_repository.sandbox.repository_url}",
      "memory": ${var.memory},
      "cpu": ${var.n_cpus},
      "environment": [
        {
          "name": "SERVICES",
          "value": "iam,lambda,apigateway,s3,dynamodb"
        },
        {
          "name": "AWS_DEFAULT_REGION",
          "value": "${var.region}"
        },
        {
          "name": "LAMBDA_EXECUTOR",
          "value": "docker"
        },
        {
          "name": "DOCKER_HOST",
          "value": "unix:///var/run/docker.sock"
        },
        {
          "name": "DEBUG",
          "value": "1"
        }
      ],
      "mountPoints": [
        {
          "containerPath": "/var/run/docker.sock",
          "sourceVolume": "dockersock"
        }
      ],
      "portMappings": [
        {
            "containerPort": ${var.localstack_port},
            "hostPort": ${var.localstack_port}
        },
        {
            "containerPort": ${var.proxy_port},
            "hostPort": ${var.proxy_port}
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
            "awslogs-group": "${var.prefix}--ecs--sandbox",
            "awslogs-region": "${var.region}",
            "awslogs-stream-prefix": "${var.prefix}--ecs--sandbox",
            "awslogs-create-group": "true"
        }
      }
    }
  ]
  DEFINITION
  requires_compatibilities = ["EC2"]
  network_mode             = "awsvpc"
  memory                   = var.memory
  cpu                      = var.n_cpus * 1024
  execution_role_arn       = aws_iam_role.ecs_task.arn
  volume {
    name      = "dockersock"
    host_path = "/var/run/docker.sock"
  }

  depends_on = [
    aws_ecr_repository.sandbox,
    aws_ecs_cluster.sandbox,
    aws_iam_role.ecs_task
  ]
}


resource "aws_ecs_service" "sandbox" {
  name            = "${var.prefix}--ecs-service--sandbox"
  cluster         = aws_ecs_cluster.sandbox.id
  task_definition = aws_ecs_task_definition.sandbox.arn
  launch_type     = "EC2"

  load_balancer {
    target_group_arn = aws_alb_target_group.sandbox.id
    container_name   = var.container_name
    container_port   = var.proxy_port
  }

  network_configuration {
    security_groups = [aws_security_group.sandbox-ecs.id]
    subnets         = aws_subnet.private.*.id
  }
  desired_count                      = 1
  deployment_minimum_healthy_percent = 0
  depends_on = [
    aws_ecs_cluster.sandbox,
    aws_ecs_task_definition.sandbox,
    aws_alb_target_group.sandbox,
    aws_subnet.private,
    aws_security_group.sandbox-ecs,
  ]
}
