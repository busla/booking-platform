# Booking Platform: Agent-First Vacation Rental
# Main Terraform configuration
#
# ⚠️ IMPORTANT: All terraform commands MUST be run via Taskfile.yaml
# Syntax: task tf:<action>:<env>
# Examples: task tf:init:dev, task tf:plan:prod, task tf:apply:dev
#
# Uses cloudposse/label/null for consistent naming. Context is passed
# from root to all child modules following CloudPosse conventions.

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.27"
    }
  }

  # Backend configuration loaded from environments/{env}/backend.hcl
  backend "s3" {}
}

provider "aws" {}

# Provider alias for us-east-1 (required for CloudFront certificates)
provider "aws" {
  alias  = "us_east_1"
  region = "us-east-1"
}

# -----------------------------------------------------------------------------
# CloudPosse Label - Root context for all modules
# -----------------------------------------------------------------------------

module "label" {
  source  = "cloudposse/label/null"
  version = "~> 0.25"

  namespace   = "booking"
  environment = var.environment

  tags = {
    Project     = "booking"
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

locals {
  # Resolve certificate ARN: direct ARN takes precedence, otherwise look up by name
  certificate_arn = var.certificate_arn != "" ? var.certificate_arn : (
    var.cert_name != "" ? data.aws_acm_certificate.wildcard[0].arn : ""
  )
}

# -----------------------------------------------------------------------------
# Data Sources
# -----------------------------------------------------------------------------

# Look up ACM certificate by domain name (must be in us-east-1 for CloudFront)
data "aws_acm_certificate" "wildcard" {
  count = var.cert_name != "" && var.certificate_arn == "" ? 1 : 0

  domain      = var.cert_name
  statuses    = ["ISSUED"]
  most_recent = true

  # CloudFront requires certificates in us-east-1
  provider = aws.us_east_1
}

# -----------------------------------------------------------------------------
# DynamoDB Tables
# -----------------------------------------------------------------------------

module "dynamodb" {
  source = "./modules/dynamodb"

  # Pass CloudPosse context - module will inherit namespace, environment, tags
  context = module.label.context
}

# -----------------------------------------------------------------------------
# AgentCore Runtime
# -----------------------------------------------------------------------------

# TODO: Enable when terraform-aws-agentcore module is fully configured
# module "agentcore" {
#   source = var.agentcore_module_path
#
#   # Pass CloudPosse context
#   context = module.label.context
#   name    = "agent"
#
#   # Agent configuration
#   bedrock_model_id = var.bedrock_model_id
#
#   # DynamoDB table references
#   dynamodb_table_arns = module.dynamodb.table_arns
# }

# -----------------------------------------------------------------------------
# Cognito Passwordless Authentication
# -----------------------------------------------------------------------------

module "cognito" {
  source = "./modules/cognito-passwordless"

  # Pass CloudPosse context
  context = module.label.context

  # SES Configuration
  ses_from_email = var.ses_from_email

  # Use verification_codes table from DynamoDB module
  verification_table_name = module.dynamodb.verification_codes_table_name
  verification_table_arn  = module.dynamodb.verification_codes_table_arn

  # Verification settings
  code_ttl_seconds = 300 # 5 minutes
  max_attempts     = 3
  code_length      = 6
}

# -----------------------------------------------------------------------------
# Static Website (S3 + CloudFront)
# -----------------------------------------------------------------------------

module "static_website" {
  source = "./modules/static-website"

  # Pass CloudPosse context
  context = module.label.context

  domain_name     = var.domain_name
  certificate_arn = local.certificate_arn
}
