# AWS CloudFront CDN configuration for Transfer Requirements Management System
# Implements optimized content delivery with advanced security and caching strategies
# Provider version: hashicorp/aws ~> 4.0

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
  }
}

# CloudFront Origin Access Identity for secure S3 access
resource "aws_cloudfront_origin_access_identity" "main" {
  comment = "OAI for ${var.project_name} ${var.environment} S3 bucket access"
}

# Primary CloudFront distribution
resource "aws_cloudfront_distribution" "main" {
  enabled             = true
  is_ipv6_enabled    = true
  http_version       = "http2and3"
  price_class        = var.price_class
  aliases            = [var.domain_name]
  web_acl_id         = var.waf_web_acl_id
  retain_on_delete   = var.environment == "prod"
  wait_for_deployment = false

  # Origin configuration for S3 bucket
  origin {
    domain_name = var.bucket_regional_domain_name
    origin_id   = "S3-${var.project_name}-${var.environment}"
    origin_path = ""

    s3_origin_config {
      origin_access_identity = aws_cloudfront_origin_access_identity.main.cloudfront_access_identity_path
    }

    origin_shield {
      enabled              = var.environment == "prod"
      origin_shield_region = data.aws_region.current.name
    }
  }

  # Default cache behavior configuration
  default_cache_behavior {
    target_origin_id       = "S3-${var.project_name}-${var.environment}"
    viewer_protocol_policy = "redirect-to-https"
    allowed_methods        = ["GET", "HEAD", "OPTIONS"]
    cached_methods         = ["GET", "HEAD"]
    compress              = true
    default_ttl           = var.default_ttl
    min_ttl              = 0
    max_ttl              = 31536000 # 1 year

    forwarded_values {
      query_string = true
      headers      = ["Origin", "Access-Control-Request-Method", "Access-Control-Request-Headers"]
      
      cookies {
        forward = "none"
      }
    }

    function_association {
      event_type   = "viewer-request"
      function_arn = aws_cloudfront_function.security_headers.arn
    }
  }

  # Custom error responses for SPA routing
  dynamic "custom_error_response" {
    for_each = [403, 404]
    content {
      error_code         = custom_error_response.value
      response_code      = 200
      response_page_path = "/index.html"
      error_caching_min_ttl = 300
    }
  }

  # Access logging configuration
  dynamic "logging_config" {
    for_each = var.logging_enabled ? [1] : []
    content {
      include_cookies = false
      bucket         = var.log_bucket
      prefix         = "cloudfront/${var.environment}"
    }
  }

  # Geographic restrictions
  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  # SSL/TLS configuration
  viewer_certificate {
    acm_certificate_arn      = var.certificate_arn
    ssl_support_method       = "sni-only"
    minimum_protocol_version = "TLSv1.2_2021"
  }

  # Tags for resource management
  tags = {
    Environment     = var.environment
    Project         = var.project_name
    ManagedBy      = "terraform"
    CreatedAt      = timestamp()
    Purpose        = "Content delivery for Transfer Requirements Management System"
    SecurityLevel  = "High"
  }
}

# CloudFront function for security headers
resource "aws_cloudfront_function" "security_headers" {
  name    = "${var.project_name}-${var.environment}-security-headers"
  runtime = "cloudfront-js-1.0"
  comment = "Adds security headers to all responses"
  publish = true
  code    = <<-EOT
    function handler(event) {
      var response = event.response;
      var headers = response.headers;
      
      headers['strict-transport-security'] = { value: 'max-age=31536000; includeSubdomains; preload'};
      headers['x-content-type-options'] = { value: 'nosniff'};
      headers['x-frame-options'] = { value: 'DENY'};
      headers['x-xss-protection'] = { value: '1; mode=block'};
      headers['referrer-policy'] = { value: 'strict-origin-when-cross-origin'};
      headers['content-security-policy'] = {
        value: "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline';"
      };
      
      return response;
    }
  EOT
}

# Current region data source
data "aws_region" "current" {}

# Cache invalidation IAM role
resource "aws_iam_role" "cloudfront_invalidation" {
  name = "${var.project_name}-${var.environment}-cf-invalidation"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "cloudfront.amazonaws.com"
        }
      }
    ]
  })

  inline_policy {
    name = "cloudfront-invalidation"
    policy = jsonencode({
      Version = "2012-10-17"
      Statement = [
        {
          Effect = "Allow"
          Action = [
            "cloudfront:CreateInvalidation"
          ]
          Resource = [aws_cloudfront_distribution.main.arn]
        }
      ]
    })
  }
}