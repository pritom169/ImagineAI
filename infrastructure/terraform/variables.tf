# -----------------------------------------------------------------------------
# Root Variables for ImagineAI Infrastructure
# -----------------------------------------------------------------------------

variable "project_name" {
  description = "Name of the project, used as a prefix for all resources"
  type        = string
  default     = "imagineai"

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{2,20}$", var.project_name))
    error_message = "Project name must be 3-21 lowercase alphanumeric characters or hyphens, starting with a letter."
  }
}

variable "environment" {
  description = "Deployment environment (dev, staging, prod)"
  type        = string

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be one of: dev, staging, prod."
  }
}

variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
  default     = "us-east-1"
}

# -----------------------------------------------------------------------------
# Networking
# -----------------------------------------------------------------------------

variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"

  validation {
    condition     = can(cidrhost(var.vpc_cidr, 0))
    error_message = "VPC CIDR must be a valid IPv4 CIDR block."
  }
}

variable "availability_zones" {
  description = "List of availability zones to use (must be exactly 3)"
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b", "us-east-1c"]

  validation {
    condition     = length(var.availability_zones) == 3
    error_message = "Exactly 3 availability zones must be specified."
  }
}

# -----------------------------------------------------------------------------
# EKS
# -----------------------------------------------------------------------------

variable "eks_cluster_version" {
  description = "Kubernetes version for the EKS cluster"
  type        = string
  default     = "1.29"
}

variable "eks_node_instance_types" {
  description = "EC2 instance types for EKS managed node group"
  type        = list(string)
  default     = ["t3.large"]
}

variable "eks_node_desired_size" {
  description = "Desired number of worker nodes"
  type        = number
  default     = 3
}

variable "eks_node_min_size" {
  description = "Minimum number of worker nodes"
  type        = number
  default     = 2
}

variable "eks_node_max_size" {
  description = "Maximum number of worker nodes"
  type        = number
  default     = 6
}

variable "eks_node_disk_size" {
  description = "Disk size in GB for worker nodes"
  type        = number
  default     = 50
}

# -----------------------------------------------------------------------------
# RDS
# -----------------------------------------------------------------------------

variable "rds_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.medium"
}

variable "rds_allocated_storage" {
  description = "Allocated storage in GB for RDS"
  type        = number
  default     = 50
}

variable "rds_max_allocated_storage" {
  description = "Maximum storage autoscaling limit in GB"
  type        = number
  default     = 200
}

variable "rds_database_name" {
  description = "Name of the initial database"
  type        = string
  default     = "imagineai"
}

variable "rds_master_username" {
  description = "Master username for the RDS instance"
  type        = string
  default     = "imagineai_admin"
  sensitive   = true
}

variable "rds_master_password" {
  description = "Master password for the RDS instance"
  type        = string
  sensitive   = true
}

variable "rds_multi_az" {
  description = "Enable Multi-AZ deployment for RDS"
  type        = bool
  default     = false
}

# -----------------------------------------------------------------------------
# ElastiCache
# -----------------------------------------------------------------------------

variable "elasticache_node_type" {
  description = "ElastiCache node type"
  type        = string
  default     = "cache.t3.medium"
}

variable "elasticache_num_cache_nodes" {
  description = "Number of cache nodes in the replication group"
  type        = number
  default     = 2
}

# -----------------------------------------------------------------------------
# S3
# -----------------------------------------------------------------------------

variable "s3_force_destroy" {
  description = "Allow destruction of non-empty S3 buckets (use with caution)"
  type        = bool
  default     = false
}

# -----------------------------------------------------------------------------
# Amazon MQ
# -----------------------------------------------------------------------------

variable "mq_instance_type" {
  description = "Amazon MQ broker instance type"
  type        = string
  default     = "mq.t3.micro"
}

variable "mq_username" {
  description = "Username for the RabbitMQ broker"
  type        = string
  default     = "imagineai"
  sensitive   = true
}

variable "mq_password" {
  description = "Password for the RabbitMQ broker"
  type        = string
  sensitive   = true
}

# -----------------------------------------------------------------------------
# ECR
# -----------------------------------------------------------------------------

variable "ecr_image_retention_count" {
  description = "Number of images to retain in each ECR repository"
  type        = number
  default     = 30
}

# -----------------------------------------------------------------------------
# Tags
# -----------------------------------------------------------------------------

variable "additional_tags" {
  description = "Additional tags to apply to all resources"
  type        = map(string)
  default     = {}
}
