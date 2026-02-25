module "imagineai" {
  source = "../../"

  project_name       = "imagineai"
  environment        = "dev"
  aws_region         = "us-east-1"
  vpc_cidr           = "10.0.0.0/16"
  availability_zones = ["us-east-1a", "us-east-1b", "us-east-1c"]

  # EKS — smaller for dev
  eks_cluster_version     = "1.29"
  eks_node_instance_types = ["t3.medium"]
  eks_node_desired_size   = 2
  eks_node_min_size       = 1
  eks_node_max_size       = 3
  eks_node_disk_size      = 30

  # RDS — minimal
  rds_instance_class        = "db.t3.micro"
  rds_allocated_storage     = 20
  rds_max_allocated_storage = 50
  rds_database_name         = "imagineai"
  rds_master_username       = var.rds_master_username
  rds_master_password       = var.rds_master_password
  rds_multi_az              = false

  # ElastiCache — single node
  elasticache_node_type       = "cache.t3.micro"
  elasticache_num_cache_nodes = 1

  # S3
  s3_force_destroy = true

  # MQ
  mq_instance_type = "mq.t3.micro"
  mq_username      = var.mq_username
  mq_password      = var.mq_password

  # ECR
  ecr_image_retention_count = 10

  additional_tags = {
    Team        = "engineering"
    CostCenter  = "development"
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
