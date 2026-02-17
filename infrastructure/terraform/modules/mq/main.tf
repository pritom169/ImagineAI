# -----------------------------------------------------------------------------
# Amazon MQ Module — RabbitMQ broker for Celery
# -----------------------------------------------------------------------------

locals {
  name_prefix = "${var.project_name}-${var.environment}"
}

resource "aws_security_group" "this" {
  name        = "${local.name_prefix}-mq-sg"
  description = "Allow RabbitMQ from EKS worker nodes"
  vpc_id      = var.vpc_id
  tags        = merge(var.tags, { Name = "${local.name_prefix}-mq-sg" })
}

resource "aws_vpc_security_group_ingress_rule" "amqp" {
  security_group_id            = aws_security_group.this.id
  description                  = "AMQPS from EKS nodes"
  from_port                    = 5671
  to_port                      = 5671
  ip_protocol                  = "tcp"
  referenced_security_group_id = var.eks_security_group_id
}

resource "aws_vpc_security_group_ingress_rule" "console" {
  security_group_id            = aws_security_group.this.id
  description                  = "RabbitMQ console from EKS nodes"
  from_port                    = 443
  to_port                      = 443
  ip_protocol                  = "tcp"
  referenced_security_group_id = var.eks_security_group_id
}

resource "aws_vpc_security_group_egress_rule" "all" {
  security_group_id = aws_security_group.this.id
  ip_protocol       = "-1"
  cidr_ipv4         = "0.0.0.0/0"
}

resource "aws_mq_broker" "this" {
  broker_name        = "${local.name_prefix}-rabbitmq"
  engine_type        = "RabbitMQ"
  engine_version     = "3.12"
  host_instance_type = var.instance_type
  deployment_mode    = "SINGLE_INSTANCE"
  publicly_accessible = false

  subnet_ids         = [var.private_subnet_ids[0]]
  security_groups    = [aws_security_group.this.id]

  auto_minor_version_upgrade = true

  user {
    username = var.username
    password = var.password
  }

  logs {
    general = true
  }

  maintenance_window_start_time {
    day_of_week = "SUNDAY"
    time_of_day = "04:00"
    time_zone   = "UTC"
  }

  tags = merge(var.tags, { Name = "${local.name_prefix}-rabbitmq" })
}
