# Development Environment Variables
# Used with: task tf:plan:dev / task tf:apply:dev

environment = "dev"
aws_region  = "us-east-1"

# AgentCore module path (set when module is available)
# agentcore_module_path = "git::https://github.com/awslabs/terraform-aws-agentcore.git"

# SES verified email for notifications (set after SES verification)
# ses_from_email = "noreply@yourdomain.com"

# Custom domain (optional - uses CloudFront default if not set)
# domain_name     = "dev.summerhouse.yourdomain.com"
# certificate_arn = "arn:aws:acm:us-east-1:ACCOUNT:certificate/CERT-ID"
