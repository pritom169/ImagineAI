output "repository_urls" {
  description = "Map of ECR repository names to their URLs"
  value       = { for k, v in aws_ecr_repository.this : k => v.repository_url }
}

output "repository_arns" {
  description = "List of ECR repository ARNs"
  value       = [for v in aws_ecr_repository.this : v.arn]
}
