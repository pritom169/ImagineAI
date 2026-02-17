module "imagineai" {
  source = "../../"

  project_name       = "imagineai"
  environment        = "staging"
  aws_region         = "us-east-1"
  vpc_cidr           = "10.1.0.0/16"
  availability_zones = ["us-east-1a", "us-east-1b", "us-east-1c"]

  # EKS
  eks_cluster_version     = "1.29"
  eks_node_instance_types = ["t3.large"]
  eks_node_desired_size   = 3
  eks_node_min_size       = 2
  eks_node_max_size       = 5
  eks_node_disk_size      = 50

  # RDS
  rds_instance_class        = "db.t3.medium"
  rds_allocated_storage     = 50
  rds_max_allocated_storage = 100
  rds_database_name         = "imagineai"
  rds_master_username       = var.rds_master_username
  rds_master_password       = var.rds_master_password
  rds_multi_az              = false

  # ElastiCache
  elasticache_node_type       = "cache.t3.medium"
  elasticache_num_cache_nodes = 2

  # S3
  s3_force_destroy = false

  # MQ
  mq_instance_type = "mq.t3.micro"
  mq_username      = var.mq_username
  mq_password      = var.mq_password

  # ECR
  ecr_image_retention_count = 20

  additional_tags = {
    Team       = "engineering"
    CostCenter = "staging"
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
