variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "environment" {
  description = "Deployment environment (dev, staging, prod)"
  type        = string
}

variable "vpc_id" {
  description = "ID of the VPC"
  type        = string
}

variable "private_subnet_ids" {
  description = "List of private subnet IDs"
  type        = list(string)
}

variable "instance_type" {
  description = "Amazon MQ broker instance type"
  type        = string
}

variable "username" {
  description = "Username for the RabbitMQ broker"
  type        = string
  sensitive   = true
}

variable "password" {
  description = "Password for the RabbitMQ broker"
  type        = string
  sensitive   = true
}

variable "eks_security_group_id" {
  description = "Security group ID of EKS worker nodes"
  type        = string
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default     = {}
}
