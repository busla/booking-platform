# Terraform Backend Configuration for Production
# Used with: terraform init -backend-config=environments/backend-prod.tfvars

bucket         = "summerhouse-terraform-state-prod"
key            = "summerhouse/prod/terraform.tfstate"
region         = "us-east-1"
encrypt        = true
dynamodb_table = "summerhouse-terraform-locks-prod"

# AWS Profile (production account)
# profile = "apro-prod"
