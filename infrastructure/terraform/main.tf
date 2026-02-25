# -----------------------------------------------------------------------------
# ImagineAI — Root Module
# Wires together all infrastructure sub-modules for the AI-powered image
# analysis platform: networking, compute, databases, caching, storage,
# messaging, container registries, and IAM roles.
# -----------------------------------------------------------------------------

locals {
  name_prefix = "${var.project_name}-${var.environment}"
  common_tags = merge(var.additional_tags, {
    Project     = var.project_name
    Environment = var.environment
  })
}

# -----------------------------------------------------------------------------
# Data Sources
# -----------------------------------------------------------------------------

data "aws_caller_identity" "current" {}
data "aws_partition" "current" {}
data "aws_region" "current" {}

# -----------------------------------------------------------------------------
# VPC — 3 public + 3 private subnets, NAT GW, IGW
# -----------------------------------------------------------------------------

module "vpc" {
  source = "./modules/vpc"

  project_name       = var.project_name
  environment        = var.environment
  vpc_cidr           = var.vpc_cidr
  availability_zones = var.availability_zones
  tags               = local.common_tags
}

# -----------------------------------------------------------------------------
# EKS — Managed Kubernetes cluster with node group
# -----------------------------------------------------------------------------

module "eks" {
  source = "./modules/eks"

  project_name        = var.project_name
  environment         = var.environment
  cluster_version     = var.eks_cluster_version
  vpc_id              = module.vpc.vpc_id
  private_subnet_ids  = module.vpc.private_subnet_ids
  node_instance_types = var.eks_node_instance_types
  node_desired_size   = var.eks_node_desired_size
  node_min_size       = var.eks_node_min_size
  node_max_size       = var.eks_node_max_size
  node_disk_size      = var.eks_node_disk_size
  tags                = local.common_tags
}

# -----------------------------------------------------------------------------
# RDS — PostgreSQL 16
# -----------------------------------------------------------------------------

module "rds" {
  source = "./modules/rds"

  project_name          = var.project_name
  environment           = var.environment
  vpc_id                = module.vpc.vpc_id
  private_subnet_ids    = module.vpc.private_subnet_ids
  instance_class        = var.rds_instance_class
  allocated_storage     = var.rds_allocated_storage
  max_allocated_storage = var.rds_max_allocated_storage
  database_name         = var.rds_database_name
  master_username       = var.rds_master_username
  master_password       = var.rds_master_password
  multi_az              = var.rds_multi_az
  eks_security_group_id = module.eks.node_security_group_id
  tags                  = local.common_tags
}

# -----------------------------------------------------------------------------
# ElastiCache — Redis 7
# -----------------------------------------------------------------------------

module "elasticache" {
  source = "./modules/elasticache"

  project_name          = var.project_name
  environment           = var.environment
  vpc_id                = module.vpc.vpc_id
  private_subnet_ids    = module.vpc.private_subnet_ids
  node_type             = var.elasticache_node_type
  num_cache_nodes       = var.elasticache_num_cache_nodes
  eks_security_group_id = module.eks.node_security_group_id
  tags                  = local.common_tags
}

# -----------------------------------------------------------------------------
# S3 — Image storage bucket
# -----------------------------------------------------------------------------

module "s3" {
  source = "./modules/s3"

  project_name  = var.project_name
  environment   = var.environment
  force_destroy = var.s3_force_destroy
  tags          = local.common_tags
}

# -----------------------------------------------------------------------------
# ECR — Container image repositories
# -----------------------------------------------------------------------------

module "ecr" {
  source = "./modules/ecr"

  project_name         = var.project_name
  environment          = var.environment
  image_retention_count = var.ecr_image_retention_count
  tags                 = local.common_tags
}

# -----------------------------------------------------------------------------
# Amazon MQ — RabbitMQ broker for Celery
# -----------------------------------------------------------------------------

module "mq" {
  source = "./modules/mq"

  project_name          = var.project_name
  environment           = var.environment
  vpc_id                = module.vpc.vpc_id
  private_subnet_ids    = module.vpc.private_subnet_ids
  instance_type         = var.mq_instance_type
  username              = var.mq_username
  password              = var.mq_password
  eks_security_group_id = module.eks.node_security_group_id
  tags                  = local.common_tags
}

# -----------------------------------------------------------------------------
# IAM — IRSA roles for EKS workloads
# -----------------------------------------------------------------------------

module "iam" {
  source = "./modules/iam"

  project_name               = var.project_name
  environment                = var.environment
  aws_account_id             = data.aws_caller_identity.current.account_id
  aws_region                 = var.aws_region
  eks_oidc_provider_arn      = module.eks.oidc_provider_arn
  eks_oidc_provider_url      = module.eks.oidc_issuer_url
  s3_bucket_arn              = module.s3.bucket_arn
  ecr_repository_arns        = module.ecr.repository_arns
  tags                       = local.common_tags
}
