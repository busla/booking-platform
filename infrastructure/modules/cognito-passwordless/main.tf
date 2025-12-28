# Cognito Passwordless Module - Main Resources
# Implements passwordless email verification using Cognito custom auth challenge
#
# Flow:
# 1. User enters email -> InitiateAuth (CUSTOM_AUTH)
# 2. DefineAuthChallenge Lambda -> Returns CUSTOM_CHALLENGE
# 3. CreateAuthChallenge Lambda -> Generates code, sends email via SES
# 4. User enters code -> RespondToAuthChallenge
# 5. VerifyAuthChallenge Lambda -> Validates code from DynamoDB
# 6. DefineAuthChallenge Lambda -> Returns tokens if valid
#
# Pattern: Single label module with context from root

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = ">= 2.0"
    }
    null = {
      source  = "hashicorp/null"
      version = ">= 3.0"
    }
  }
}

# -----------------------------------------------------------------------------
# CloudPosse Label - inherits context from root, sets component name
# -----------------------------------------------------------------------------

module "label" {
  source  = "cloudposse/label/null"
  version = "~> 0.25"

  # Inherit namespace, environment, tags from root context
  context = var.context

  # Component name for this module
  name = "auth"
}

locals {
  lambda_runtime = "nodejs20.x"
  lambdas_dir    = "${path.module}/lambdas"
}

data "aws_region" "current" {}
data "aws_caller_identity" "current" {}

# Note: Uses existing verification_codes table from dynamodb module
# Table is passed in via var.verification_table_name and var.verification_table_arn

# -----------------------------------------------------------------------------
# IAM Role for Lambda Functions (using terraform-aws-modules/iam)
# -----------------------------------------------------------------------------

module "lambda_role" {
  source  = "terraform-aws-modules/iam/aws//modules/iam-role"
  version = "~> 6.0"

  create = true
  name   = "${module.label.id}-lambda"

  # Lambda service can assume this role
  trust_policy_permissions = {
    LambdaServiceTrust = {
      principals = [{
        type        = "Service"
        identifiers = ["lambda.amazonaws.com"]
      }]
    }
  }

  # Attach custom policy
  policies = {
    lambda = module.lambda_policy.arn
  }

  tags = module.label.tags
}

module "lambda_policy" {
  source  = "terraform-aws-modules/iam/aws//modules/iam-policy"
  version = "~> 6.0"

  name        = "${module.label.id}-lambda-policy"
  path        = "/"
  description = "Policy for Cognito passwordless Lambda functions"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "CloudWatchLogs"
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:${data.aws_region.current.id}:${data.aws_caller_identity.current.account_id}:*"
      },
      {
        Sid    = "DynamoDBVerificationCodes"
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem"
        ]
        Resource = var.verification_table_arn
      },
      {
        Sid      = "SESSendEmail"
        Effect   = "Allow"
        Action   = "ses:SendEmail"
        Resource = "*"
        Condition = {
          StringEquals = {
            "ses:FromAddress" = var.ses_from_email
          }
        }
      }
    ]
  })

  tags = module.label.tags
}

# -----------------------------------------------------------------------------
# Lambda: Define Auth Challenge (no dependencies)
# -----------------------------------------------------------------------------

data "archive_file" "define_auth_challenge" {
  type        = "zip"
  source_dir  = "${local.lambdas_dir}/define-auth-challenge"
  output_path = "${path.module}/.terraform/define-auth-challenge.zip"
}

resource "aws_lambda_function" "define_auth_challenge" {
  function_name    = "${module.label.id}-define-auth"
  role             = module.lambda_role.arn
  handler          = "index.handler"
  runtime          = local.lambda_runtime
  filename         = data.archive_file.define_auth_challenge.output_path
  source_code_hash = data.archive_file.define_auth_challenge.output_base64sha256
  timeout          = 10

  tags = module.label.tags
}

resource "aws_lambda_permission" "define_auth_challenge" {
  statement_id  = "AllowCognitoInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.define_auth_challenge.function_name
  principal     = "cognito-idp.amazonaws.com"
  source_arn    = aws_cognito_user_pool.main.arn
}

# -----------------------------------------------------------------------------
# Lambda: Create Auth Challenge (has npm dependencies)
# -----------------------------------------------------------------------------

resource "null_resource" "create_auth_challenge_deps" {
  triggers = {
    package_json = filemd5("${local.lambdas_dir}/create-auth-challenge/package.json")
    source_code  = filemd5("${local.lambdas_dir}/create-auth-challenge/index.mjs")
  }

  provisioner "local-exec" {
    command     = "npm ci --omit=dev"
    working_dir = "${local.lambdas_dir}/create-auth-challenge"
  }
}

data "archive_file" "create_auth_challenge" {
  type        = "zip"
  source_dir  = "${local.lambdas_dir}/create-auth-challenge"
  output_path = "${path.module}/.terraform/create-auth-challenge.zip"

  depends_on = [null_resource.create_auth_challenge_deps]
}

resource "aws_lambda_function" "create_auth_challenge" {
  function_name    = "${module.label.id}-create-auth"
  role             = module.lambda_role.arn
  handler          = "index.handler"
  runtime          = local.lambda_runtime
  filename         = data.archive_file.create_auth_challenge.output_path
  source_code_hash = data.archive_file.create_auth_challenge.output_base64sha256
  timeout          = 30

  environment {
    variables = {
      VERIFICATION_TABLE = var.verification_table_name
      FROM_EMAIL         = var.ses_from_email
      CODE_TTL           = tostring(var.code_ttl_seconds)
      CODE_LENGTH        = tostring(var.code_length)
      MAX_ATTEMPTS       = tostring(var.max_attempts)
    }
  }

  tags = module.label.tags
}

resource "aws_lambda_permission" "create_auth_challenge" {
  statement_id  = "AllowCognitoInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.create_auth_challenge.function_name
  principal     = "cognito-idp.amazonaws.com"
  source_arn    = aws_cognito_user_pool.main.arn
}

# -----------------------------------------------------------------------------
# Lambda: Verify Auth Challenge (has npm dependencies)
# -----------------------------------------------------------------------------

resource "null_resource" "verify_auth_challenge_deps" {
  triggers = {
    package_json = filemd5("${local.lambdas_dir}/verify-auth-challenge/package.json")
    source_code  = filemd5("${local.lambdas_dir}/verify-auth-challenge/index.mjs")
  }

  provisioner "local-exec" {
    command     = "npm ci --omit=dev"
    working_dir = "${local.lambdas_dir}/verify-auth-challenge"
  }
}

data "archive_file" "verify_auth_challenge" {
  type        = "zip"
  source_dir  = "${local.lambdas_dir}/verify-auth-challenge"
  output_path = "${path.module}/.terraform/verify-auth-challenge.zip"

  depends_on = [null_resource.verify_auth_challenge_deps]
}

resource "aws_lambda_function" "verify_auth_challenge" {
  function_name    = "${module.label.id}-verify-auth"
  role             = module.lambda_role.arn
  handler          = "index.handler"
  runtime          = local.lambda_runtime
  filename         = data.archive_file.verify_auth_challenge.output_path
  source_code_hash = data.archive_file.verify_auth_challenge.output_base64sha256
  timeout          = 10

  environment {
    variables = {
      VERIFICATION_TABLE = var.verification_table_name
      MAX_ATTEMPTS       = tostring(var.max_attempts)
    }
  }

  tags = module.label.tags
}

resource "aws_lambda_permission" "verify_auth_challenge" {
  statement_id  = "AllowCognitoInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.verify_auth_challenge.function_name
  principal     = "cognito-idp.amazonaws.com"
  source_arn    = aws_cognito_user_pool.main.arn
}

# -----------------------------------------------------------------------------
# Lambda: Pre Sign Up (no dependencies)
# -----------------------------------------------------------------------------

data "archive_file" "pre_sign_up" {
  type        = "zip"
  source_dir  = "${local.lambdas_dir}/pre-sign-up"
  output_path = "${path.module}/.terraform/pre-sign-up.zip"
}

resource "aws_lambda_function" "pre_sign_up" {
  function_name    = "${module.label.id}-pre-signup"
  role             = module.lambda_role.arn
  handler          = "index.handler"
  runtime          = local.lambda_runtime
  filename         = data.archive_file.pre_sign_up.output_path
  source_code_hash = data.archive_file.pre_sign_up.output_base64sha256
  timeout          = 10

  tags = module.label.tags
}

resource "aws_lambda_permission" "pre_sign_up" {
  statement_id  = "AllowCognitoInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.pre_sign_up.function_name
  principal     = "cognito-idp.amazonaws.com"
  source_arn    = aws_cognito_user_pool.main.arn
}

# -----------------------------------------------------------------------------
# Cognito User Pool
# -----------------------------------------------------------------------------

resource "aws_cognito_user_pool" "main" {
  name = "${module.label.id}-users"

  # Use email as username
  username_attributes      = ["email"]
  auto_verified_attributes = ["email"]

  # Password policy (minimal since we use passwordless)
  password_policy {
    minimum_length                   = 8
    require_lowercase                = false
    require_numbers                  = false
    require_symbols                  = false
    require_uppercase                = false
    temporary_password_validity_days = 7
  }

  # Schema - email is standard, add custom attributes as needed
  schema {
    name                = "email"
    attribute_data_type = "String"
    required            = true
    mutable             = true
    string_attribute_constraints {
      min_length = 1
      max_length = 256
    }
  }

  # Lambda triggers for custom auth
  lambda_config {
    define_auth_challenge          = aws_lambda_function.define_auth_challenge.arn
    create_auth_challenge          = aws_lambda_function.create_auth_challenge.arn
    verify_auth_challenge_response = aws_lambda_function.verify_auth_challenge.arn
    pre_sign_up                    = aws_lambda_function.pre_sign_up.arn
  }

  # Account recovery via email
  account_recovery_setting {
    recovery_mechanism {
      name     = "verified_email"
      priority = 1
    }
  }

  tags = module.label.tags
}

# -----------------------------------------------------------------------------
# Cognito User Pool Client
# -----------------------------------------------------------------------------

resource "aws_cognito_user_pool_client" "main" {
  name         = "${module.label.id}-client"
  user_pool_id = aws_cognito_user_pool.main.id

  # Auth flows - enable custom auth for passwordless
  explicit_auth_flows = [
    "ALLOW_CUSTOM_AUTH",
    "ALLOW_REFRESH_TOKEN_AUTH",
    "ALLOW_USER_SRP_AUTH"
  ]

  # Token validity
  access_token_validity  = 1  # hours
  id_token_validity      = 1  # hours
  refresh_token_validity = 30 # days

  token_validity_units {
    access_token  = "hours"
    id_token      = "hours"
    refresh_token = "days"
  }

  # Security
  prevent_user_existence_errors = "ENABLED"
  enable_token_revocation       = true

  # No client secret for public client (frontend)
  generate_secret = false
}
