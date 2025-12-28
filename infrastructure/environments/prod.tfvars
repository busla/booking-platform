# Production Environment Variables
# Used with: task tf:plan:prod / task tf:apply:prod

environment = "prod"
aws_region  = "us-east-1"

# AgentCore module path (set when module is available)
# agentcore_module_path = "git::https://github.com/awslabs/terraform-aws-agentcore.git"

# SES verified email for notifications (required for production)
# ses_from_email = "noreply@yourdomain.com"

# Custom domain (recommended for production)
# domain_name     = "summerhouse.yourdomain.com"
# certificate_arn = "arn:aws:acm:us-east-1:ACCOUNT:certificate/CERT-ID"
