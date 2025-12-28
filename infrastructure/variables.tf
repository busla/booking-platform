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

variable "agentcore_module_path" {
  description = "Path to terraform-aws-agentcore module (local or git)"
  type        = string
  default     = ""
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
