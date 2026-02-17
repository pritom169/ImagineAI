variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "environment" {
  description = "Deployment environment (dev, staging, prod)"
  type        = string
}

variable "aws_account_id" {
  description = "AWS account ID"
  type        = string
}

variable "aws_region" {
  description = "AWS region"
  type        = string
}

variable "eks_oidc_provider_arn" {
  description = "ARN of the EKS OIDC provider"
  type        = string
}

variable "eks_oidc_provider_url" {
  description = "URL of the EKS OIDC provider"
  type        = string
}

variable "s3_bucket_arn" {
  description = "ARN of the S3 images bucket"
  type        = string
}

variable "ecr_repository_arns" {
  description = "List of ECR repository ARNs"
  type        = list(string)
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default     = {}
}
