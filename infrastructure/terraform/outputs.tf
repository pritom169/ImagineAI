# -----------------------------------------------------------------------------
# Root Outputs — ImagineAI Infrastructure
# -----------------------------------------------------------------------------

# VPC
output "vpc_id" {
  description = "ID of the VPC"
  value       = module.vpc.vpc_id
}

output "vpc_cidr_block" {
  description = "CIDR block of the VPC"
  value       = module.vpc.vpc_cidr_block
}

output "public_subnet_ids" {
  description = "IDs of the public subnets"
  value       = module.vpc.public_subnet_ids
}

output "private_subnet_ids" {
  description = "IDs of the private subnets"
  value       = module.vpc.private_subnet_ids
}

# EKS
output "eks_cluster_name" {
  description = "Name of the EKS cluster"
  value       = module.eks.cluster_name
}

output "eks_cluster_endpoint" {
  description = "Endpoint for the EKS cluster API server"
  value       = module.eks.cluster_endpoint
}

output "eks_cluster_certificate_authority" {
  description = "Base64 encoded certificate data for cluster authentication"
  value       = module.eks.cluster_certificate_authority_data
  sensitive   = true
}

output "eks_kubeconfig_command" {
  description = "AWS CLI command to update kubeconfig"
  value       = "aws eks update-kubeconfig --region ${var.aws_region} --name ${module.eks.cluster_name}"
}

# RDS
output "rds_endpoint" {
  description = "Connection endpoint for the RDS instance"
  value       = module.rds.endpoint
}

output "rds_database_name" {
  description = "Name of the default database"
  value       = module.rds.database_name
}

output "rds_port" {
  description = "Port of the RDS instance"
  value       = module.rds.port
}

# ElastiCache
output "elasticache_primary_endpoint" {
  description = "Primary endpoint for the Redis replication group"
  value       = module.elasticache.primary_endpoint_address
}

output "elasticache_reader_endpoint" {
  description = "Reader endpoint for the Redis replication group"
  value       = module.elasticache.reader_endpoint_address
}

output "elasticache_port" {
  description = "Port for Redis connections"
  value       = module.elasticache.port
}

# S3
output "s3_bucket_name" {
  description = "Name of the S3 images bucket"
  value       = module.s3.bucket_name
}

output "s3_bucket_arn" {
  description = "ARN of the S3 images bucket"
  value       = module.s3.bucket_arn
}

output "s3_bucket_domain_name" {
  description = "Domain name of the S3 images bucket"
  value       = module.s3.bucket_domain_name
}

# ECR
output "ecr_repository_urls" {
  description = "Map of ECR repository names to their URLs"
  value       = module.ecr.repository_urls
}

# Amazon MQ
output "mq_broker_id" {
  description = "ID of the Amazon MQ broker"
  value       = module.mq.broker_id
}

output "mq_broker_amqp_endpoint" {
  description = "AMQP endpoint for the RabbitMQ broker"
  value       = module.mq.amqp_endpoint
}

output "mq_broker_console_url" {
  description = "Web console URL for the RabbitMQ broker"
  value       = module.mq.console_url
}

# IAM
output "iam_api_role_arn" {
  description = "ARN of the IAM role for the API service (S3 access)"
  value       = module.iam.api_role_arn
}

output "iam_worker_role_arn" {
  description = "ARN of the IAM role for Celery workers (Bedrock access)"
  value       = module.iam.worker_role_arn
}

output "iam_ecr_pull_role_arn" {
  description = "ARN of the IAM role for ECR image pulling"
  value       = module.iam.ecr_pull_role_arn
}
