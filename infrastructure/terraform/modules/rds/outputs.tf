output "endpoint" {
  description = "Connection endpoint for the RDS instance"
  value       = aws_db_instance.this.endpoint
}

output "database_name" {
  description = "Name of the default database"
  value       = aws_db_instance.this.db_name
}

output "port" {
  description = "Port of the RDS instance"
  value       = aws_db_instance.this.port
}

output "instance_id" {
  description = "Identifier of the RDS instance"
  value       = aws_db_instance.this.id
}

output "address" {
  description = "Hostname of the RDS instance"
  value       = aws_db_instance.this.address
}
