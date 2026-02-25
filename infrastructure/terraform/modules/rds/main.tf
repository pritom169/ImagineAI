# -----------------------------------------------------------------------------
# RDS Module — PostgreSQL 16 with encryption, backups, monitoring
# -----------------------------------------------------------------------------

locals {
  name_prefix = "${var.project_name}-${var.environment}"
  port        = 5432
}

resource "aws_db_subnet_group" "this" {
  name        = "${local.name_prefix}-db-subnet-group"
  description = "Private subnets for ${local.name_prefix} RDS"
  subnet_ids  = var.private_subnet_ids
  tags        = merge(var.tags, { Name = "${local.name_prefix}-db-subnet-group" })
}

resource "aws_security_group" "this" {
  name        = "${local.name_prefix}-rds-sg"
  description = "Allow PostgreSQL from EKS worker nodes"
  vpc_id      = var.vpc_id
  tags        = merge(var.tags, { Name = "${local.name_prefix}-rds-sg" })

  lifecycle { create_before_destroy = true }
}

resource "aws_vpc_security_group_ingress_rule" "postgres_from_eks" {
  security_group_id            = aws_security_group.this.id
  description                  = "PostgreSQL from EKS nodes"
  from_port                    = local.port
  to_port                      = local.port
  ip_protocol                  = "tcp"
  referenced_security_group_id = var.eks_security_group_id
}

resource "aws_vpc_security_group_egress_rule" "all" {
  security_group_id = aws_security_group.this.id
  ip_protocol       = "-1"
  cidr_ipv4         = "0.0.0.0/0"
}

resource "aws_db_parameter_group" "this" {
  name   = "${local.name_prefix}-pg16-params"
  family = "postgres16"

  parameter {
    name         = "rds.force_ssl"
    value        = "1"
    apply_method = "pending-reboot"
  }

  parameter {
    name         = "log_min_duration_statement"
    value        = "1000"
    apply_method = "immediate"
  }

  parameter {
    name         = "shared_preload_libraries"
    value        = "pg_stat_statements"
    apply_method = "pending-reboot"
  }

  tags = var.tags
  lifecycle { create_before_destroy = true }
}

resource "aws_db_instance" "this" {
  identifier = "${local.name_prefix}-postgres"

  engine               = "postgres"
  engine_version       = "16"
  instance_class       = var.instance_class
  parameter_group_name = aws_db_parameter_group.this.name

  allocated_storage     = var.allocated_storage
  max_allocated_storage = var.max_allocated_storage > 0 ? var.max_allocated_storage : null
  storage_type          = "gp3"
  storage_encrypted     = true

  db_name  = var.database_name
  username = var.master_username
  password = var.master_password
  port     = local.port

  db_subnet_group_name   = aws_db_subnet_group.this.name
  vpc_security_group_ids = [aws_security_group.this.id]
  publicly_accessible    = false
  multi_az               = var.multi_az

  backup_retention_period = var.environment == "prod" ? 30 : 7
  backup_window           = "03:00-04:00"
  maintenance_window      = "sun:04:30-sun:05:30"
  copy_tags_to_snapshot   = true

  performance_insights_enabled          = true
  performance_insights_retention_period = var.environment == "prod" ? 731 : 7
  enabled_cloudwatch_logs_exports       = ["postgresql", "upgrade"]

  deletion_protection       = var.environment == "prod"
  skip_final_snapshot       = var.environment == "dev"
  final_snapshot_identifier = var.environment != "dev" ? "${local.name_prefix}-final" : null

  auto_minor_version_upgrade = true
  apply_immediately          = var.environment == "dev"

  tags = merge(var.tags, { Name = "${local.name_prefix}-postgres" })
}
