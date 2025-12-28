# Summerhouse Infrastructure Outputs

# DynamoDB Table Outputs
output "dynamodb_reservations_table_name" {
  description = "Name of the reservations DynamoDB table"
  value       = module.dynamodb.reservations_table_name
}

output "dynamodb_guests_table_name" {
  description = "Name of the guests DynamoDB table"
  value       = module.dynamodb.guests_table_name
}

output "dynamodb_availability_table_name" {
  description = "Name of the availability DynamoDB table"
  value       = module.dynamodb.availability_table_name
}

output "dynamodb_pricing_table_name" {
  description = "Name of the pricing DynamoDB table"
  value       = module.dynamodb.pricing_table_name
}

output "dynamodb_payments_table_name" {
  description = "Name of the payments DynamoDB table"
  value       = module.dynamodb.payments_table_name
}

output "dynamodb_verification_codes_table_name" {
  description = "Name of the verification codes DynamoDB table"
  value       = module.dynamodb.verification_codes_table_name
}

# Cognito Outputs (uncomment when cognito-passwordless module is available)
# output "cognito_user_pool_id" {
#   description = "Cognito User Pool ID"
#   value       = module.cognito.user_pool_id
# }
#
# output "cognito_user_pool_client_id" {
#   description = "Cognito User Pool Client ID"
#   value       = module.cognito.user_pool_client_id
# }

# AgentCore Outputs (uncomment when agentcore module is configured)
# output "agentcore_endpoint" {
#   description = "AgentCore Runtime endpoint URL"
#   value       = module.agentcore.endpoint_url
# }

# Static Website Outputs (uncomment when static-website module is available)
# output "cloudfront_distribution_id" {
#   description = "CloudFront distribution ID"
#   value       = module.static_website.distribution_id
# }
#
# output "cloudfront_domain_name" {
#   description = "CloudFront distribution domain name"
#   value       = module.static_website.domain_name
# }
#
# output "s3_bucket_name" {
#   description = "S3 bucket name for frontend assets"
#   value       = module.static_website.bucket_name
# }
