# DynamoDB Module Outputs

output "reservations_table_name" {
  description = "Name of the reservations table"
  value       = aws_dynamodb_table.reservations.name
}

output "reservations_table_arn" {
  description = "ARN of the reservations table"
  value       = aws_dynamodb_table.reservations.arn
}

output "guests_table_name" {
  description = "Name of the guests table"
  value       = aws_dynamodb_table.guests.name
}

output "guests_table_arn" {
  description = "ARN of the guests table"
  value       = aws_dynamodb_table.guests.arn
}

output "availability_table_name" {
  description = "Name of the availability table"
  value       = aws_dynamodb_table.availability.name
}

output "availability_table_arn" {
  description = "ARN of the availability table"
  value       = aws_dynamodb_table.availability.arn
}

output "pricing_table_name" {
  description = "Name of the pricing table"
  value       = aws_dynamodb_table.pricing.name
}

output "pricing_table_arn" {
  description = "ARN of the pricing table"
  value       = aws_dynamodb_table.pricing.arn
}

output "payments_table_name" {
  description = "Name of the payments table"
  value       = aws_dynamodb_table.payments.name
}

output "payments_table_arn" {
  description = "ARN of the payments table"
  value       = aws_dynamodb_table.payments.arn
}

output "verification_codes_table_name" {
  description = "Name of the verification codes table"
  value       = aws_dynamodb_table.verification_codes.name
}

output "verification_codes_table_arn" {
  description = "ARN of the verification codes table"
  value       = aws_dynamodb_table.verification_codes.arn
}

output "table_arns" {
  description = "List of all table ARNs for IAM policies"
  value = [
    aws_dynamodb_table.reservations.arn,
    aws_dynamodb_table.guests.arn,
    aws_dynamodb_table.availability.arn,
    aws_dynamodb_table.pricing.arn,
    aws_dynamodb_table.payments.arn,
    aws_dynamodb_table.verification_codes.arn,
  ]
}
