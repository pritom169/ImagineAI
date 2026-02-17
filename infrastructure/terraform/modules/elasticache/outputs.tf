output "primary_endpoint_address" {
  description = "Primary endpoint for the Redis replication group"
  value       = aws_elasticache_replication_group.this.primary_endpoint_address
}

output "reader_endpoint_address" {
  description = "Reader endpoint for the Redis replication group"
  value       = aws_elasticache_replication_group.this.reader_endpoint_address
}

output "port" {
  description = "Port for Redis connections"
  value       = aws_elasticache_replication_group.this.port
}
