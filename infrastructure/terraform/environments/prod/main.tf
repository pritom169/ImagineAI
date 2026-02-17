module "imagineai" {
  source = "../../"

  project_name       = "imagineai"
  environment        = "prod"
  aws_region         = "us-east-1"
  vpc_cidr           = "10.2.0.0/16"
  availability_zones = ["us-east-1a", "us-east-1b", "us-east-1c"]

  # EKS — production sizing
  eks_cluster_version     = "1.29"
  eks_node_instance_types = ["t3.xlarge"]
  eks_node_desired_size   = 4
  eks_node_min_size       = 3
  eks_node_max_size       = 8
  eks_node_disk_size      = 100

  # RDS — production with Multi-AZ
  rds_instance_class        = "db.r6g.large"
  rds_allocated_storage     = 100
  rds_max_allocated_storage = 500
  rds_database_name         = "imagineai"
  rds_master_username       = var.rds_master_username
  rds_master_password       = var.rds_master_password
  rds_multi_az              = true

  # ElastiCache — multi-node
  elasticache_node_type       = "cache.r6g.large"
  elasticache_num_cache_nodes = 3

  # S3
  s3_force_destroy = false

  # MQ
  mq_instance_type = "mq.m5.large"
  mq_username      = var.mq_username
  mq_password      = var.mq_password

  # ECR
  ecr_image_retention_count = 50

  additional_tags = {
    Team       = "engineering"
    CostCenter = "production"
  }
}

variable "rds_master_username" {
  type      = string
  sensitive = true
}

variable "rds_master_password" {
  type      = string
  sensitive = true
}

variable "mq_username" {
  type      = string
  sensitive = true
}

variable "mq_password" {
  type      = string
  sensitive = true
}
