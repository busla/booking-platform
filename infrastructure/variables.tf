# Summerhouse Infrastructure Variables

variable "environment" {
  description = "Deployment environment (dev, prod)"
  type        = string

  validation {
    condition     = contains(["dev", "prod"], var.environment)
    error_message = "Environment must be 'dev' or 'prod'."
  }
}

variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "us-east-1"
}

variable "bedrock_model_id" {
  description = "Amazon Bedrock model ID for the agent"
  type        = string
  default     = "anthropic.claude-sonnet-4-20250514"
}

variable "ses_from_email" {
  description = "Verified SES email address for sending verification codes"
  type        = string
  default     = ""
}

variable "domain_name" {
  description = "Domain name for the frontend (optional, uses CloudFront default if not set)"
  type        = string
  default     = ""
}

variable "certificate_arn" {
  description = "ACM certificate ARN for custom domain (required if domain_name is set)"
  type        = string
  default     = ""
}

variable "cert_name" {
  description = "Domain name of the ACM certificate and Route53 hosted zone (e.g., 'example.com')"
  type        = string
}

variable "hosted_zone_id" {
  description = "Route53 hosted zone ID for DNS records (required for custom domain)"
  type        = string
  default     = ""
}

# -----------------------------------------------------------------------------
# AgentCore Configuration
# -----------------------------------------------------------------------------

variable "agentcore_idle_session_ttl" {
  description = "Idle session TTL in seconds for AgentCore Runtime"
  type        = number
  default     = 3600
}

variable "agentcore_max_tokens" {
  description = "Maximum tokens for agent responses"
  type        = number
  default     = 4096
}

variable "agentcore_temperature" {
  description = "Model temperature for agent responses"
  type        = number
  default     = 0.7
}

variable "enable_agentcore_memory" {
  description = "Whether to enable AgentCore Memory for conversation state"
  type        = bool
  default     = true
}

variable "enable_agentcore_observability" {
  description = "Whether to enable AgentCore observability (CloudWatch metrics/alarms)"
  type        = bool
  default     = true
}

# -----------------------------------------------------------------------------
# Anonymous User Configuration
# -----------------------------------------------------------------------------

variable "anonymous_user_email" {
  description = <<-EOT
    Email address for the shared anonymous user. All anonymous visitors authenticate
    as this single shared user via Cognito custom auth (1 MAU cost regardless of traffic).

    The JWT for this user has email_verified=false, allowing tools to distinguish
    anonymous users from verified users and gate booking operations accordingly.

    Example: "anonymous@guest.local"
    Leave empty to disable anonymous access.
  EOT
  type        = string
  default     = "anonymous@guest.local"
}
