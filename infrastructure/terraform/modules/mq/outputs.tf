output "broker_id" {
  description = "ID of the Amazon MQ broker"
  value       = aws_mq_broker.this.id
}

output "amqp_endpoint" {
  description = "AMQP endpoint for the RabbitMQ broker"
  value       = tolist(aws_mq_broker.this.instances[0].endpoints)[0]
}

output "console_url" {
  description = "Web console URL for the RabbitMQ broker"
  value       = aws_mq_broker.this.instances[0].console_url
}
