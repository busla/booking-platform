# Terraform Backend Configuration for Development
# Used with: terraform init -backend-config=environments/backend-dev.tfvars

bucket         = "summerhouse-terraform-state-dev"
key            = "summerhouse/dev/terraform.tfstate"
region         = "us-east-1"
encrypt        = true
dynamodb_table = "summerhouse-terraform-locks-dev"

# AWS Profile (apro-sandbox for dev)
# profile = "apro-sandbox"
