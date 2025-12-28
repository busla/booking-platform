# Cognito Passwordless Module - Outputs

output "user_pool_id" {
  description = "Cognito User Pool ID"
  value       = aws_cognito_user_pool.main.id
}

output "user_pool_arn" {
  description = "Cognito User Pool ARN"
  value       = aws_cognito_user_pool.main.arn
}

output "user_pool_endpoint" {
  description = "Cognito User Pool endpoint"
  value       = aws_cognito_user_pool.main.endpoint
}

output "client_id" {
  description = "Cognito User Pool Client ID"
  value       = aws_cognito_user_pool_client.main.id
}

output "discovery_url" {
  description = "OpenID Connect discovery URL for JWT validation"
  value       = "https://cognito-idp.${data.aws_region.current.id}.amazonaws.com/${aws_cognito_user_pool.main.id}/.well-known/openid-configuration"
}

output "issuer_url" {
  description = "JWT issuer URL"
  value       = "https://cognito-idp.${data.aws_region.current.id}.amazonaws.com/${aws_cognito_user_pool.main.id}"
}

# Note: verification_table_name and verification_table_arn are now inputs from dynamodb module
# Note: data "aws_region" "current" is defined in main.tf
