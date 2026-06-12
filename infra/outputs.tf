output "orders_table_name" {
  description = "Name of the DynamoDB orders table."
  value       = aws_dynamodb_table.orders.name
}

output "orders_table_stream_arn" {
  description = "ARN of the DynamoDB orders table stream."
  value       = aws_dynamodb_table.orders.stream_arn
}
