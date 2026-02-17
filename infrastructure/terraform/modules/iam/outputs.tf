output "api_role_arn" {
  description = "ARN of the IAM role for the API service"
  value       = aws_iam_role.api.arn
}

output "worker_role_arn" {
  description = "ARN of the IAM role for Celery workers"
  value       = aws_iam_role.worker.arn
}

output "ecr_pull_role_arn" {
  description = "ARN of the IAM role for ECR image pulling"
  value       = aws_iam_role.ecr_pull.arn
}
