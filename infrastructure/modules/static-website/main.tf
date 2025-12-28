# Static Website Module - Main Resources
# Hosts Next.js static export via S3 + CloudFront
#
# Architecture:
# - S3 bucket with private access (no public access)
# - CloudFront distribution with Origin Access Control (OAC)
# - Custom domain with ACM certificate
# - Configured for SPA routing (errors -> index.html)
#
# Pattern: Single label module with context from root

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0"
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
  name = "website"
}

locals {
  s3_origin_id = "${module.label.id}-s3-origin"
}

data "aws_region" "current" {}
data "aws_caller_identity" "current" {}

# -----------------------------------------------------------------------------
# S3 Bucket for Static Files (using terraform-aws-modules/s3-bucket)
# -----------------------------------------------------------------------------

module "s3_bucket" {
  source  = "terraform-aws-modules/s3-bucket/aws"
  version = "~> 5.0"

  bucket = module.label.id

  # Versioning
  versioning = {
    enabled = true
  }

  # Server-side encryption
  server_side_encryption_configuration = {
    rule = {
      apply_server_side_encryption_by_default = {
        sse_algorithm = "AES256"
      }
    }
  }

  # Block all public access - CloudFront uses OAC
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true

  # Bucket policy for CloudFront OAC
  attach_policy = true
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "AllowCloudFrontOAC"
        Effect    = "Allow"
        Principal = { Service = "cloudfront.amazonaws.com" }
        Action    = "s3:GetObject"
        Resource  = "arn:aws:s3:::${module.label.id}/*"
        Condition = {
          StringEquals = {
            "AWS:SourceArn" = module.cloudfront.cloudfront_distribution_arn
          }
        }
      }
    ]
  })

  # Object ownership
  control_object_ownership = true
  object_ownership         = "BucketOwnerEnforced"

  tags = module.label.tags
}

# -----------------------------------------------------------------------------
# CloudFront Distribution (using terraform-aws-modules/cloudfront)
# -----------------------------------------------------------------------------

module "cloudfront" {
  source  = "terraform-aws-modules/cloudfront/aws"
  version = "~> 6.0"

  aliases             = var.domain_name != "" ? [var.domain_name] : []
  comment             = "${module.label.id} static website"
  enabled             = true
  is_ipv6_enabled     = true
  price_class         = var.price_class
  default_root_object = var.index_document

  # Origin Access Control for S3
  origin_access_control = {
    s3_oac = {
      description      = "OAC for ${module.label.id}"
      origin_type      = "s3"
      signing_behavior = "always"
      signing_protocol = "sigv4"
    }
  }

  # S3 Origin
  origin = {
    s3_origin = {
      domain_name           = module.s3_bucket.s3_bucket_bucket_regional_domain_name
      origin_access_control = "s3_oac"
    }
  }

  # Default cache behavior
  default_cache_behavior = {
    target_origin_id       = "s3_origin"
    viewer_protocol_policy = "redirect-to-https"

    allowed_methods = ["GET", "HEAD", "OPTIONS"]
    cached_methods  = ["GET", "HEAD"]
    compress        = true

    # Use managed cache policy for simple static content
    use_forwarded_values = true
    query_string         = false
    cookies_forward      = "none"

    min_ttl     = 0
    default_ttl = 3600  # 1 hour
    max_ttl     = 86400 # 24 hours
  }

  # Cache behavior for static assets (longer TTL)
  ordered_cache_behavior = [
    {
      path_pattern           = "_next/static/*"
      target_origin_id       = "s3_origin"
      viewer_protocol_policy = "redirect-to-https"

      allowed_methods = ["GET", "HEAD"]
      cached_methods  = ["GET", "HEAD"]
      compress        = true

      use_forwarded_values = true
      query_string         = false
      cookies_forward      = "none"

      min_ttl     = 0
      default_ttl = 31536000 # 1 year
      max_ttl     = 31536000
    }
  ]

  # SPA routing: Return index.html for 404s and 403s (client-side routing)
  custom_error_response = [
    {
      error_code            = 404
      response_code         = 200
      response_page_path    = "/${var.index_document}"
      error_caching_min_ttl = 10
    },
    {
      error_code            = 403
      response_code         = 200
      response_page_path    = "/${var.index_document}"
      error_caching_min_ttl = 10
    }
  ]

  # No geo restrictions
  restrictions = {
    geo_restriction = {
      restriction_type = "none"
      locations        = []
    }
  }

  # SSL/TLS certificate
  viewer_certificate = var.certificate_arn != "" ? {
    acm_certificate_arn      = var.certificate_arn
    ssl_support_method       = "sni-only"
    minimum_protocol_version = "TLSv1.2_2021"
  } : {
    cloudfront_default_certificate = true
    minimum_protocol_version       = "TLSv1"
  }

  tags = module.label.tags
}
