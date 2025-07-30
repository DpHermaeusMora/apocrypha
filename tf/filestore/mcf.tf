resource "aws_cloudfront_origin_access_control" "s3" {
  name                              = "${var.SERVICE_PREFIX[terraform.workspace]}-oac-s3"
  description                       = "Managed by Terraform"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

resource "aws_cloudfront_distribution" "mcf" {
  enabled = true
  aliases = [var.MEDIA_CDN_FQDN[terraform.workspace]]
  price_class = "PriceClass_200"
  
  origin {
    domain_name              = data.aws_s3_bucket.mb.bucket_regional_domain_name
    origin_id                = "s3Primary"
    origin_access_control_id = aws_cloudfront_origin_access_control.s3.id
  }
  
  // All values are defaults from the AWS console.
  default_cache_behavior {
    viewer_protocol_policy = "allow-all"
    compress               = true
    allowed_methods        = ["GET", "HEAD"]
    cached_methods         = ["GET", "HEAD"]
    target_origin_id       = "s3Primary"
    min_ttl                = 0
    default_ttl            = 3600
    max_ttl                = 86400

    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
      headers   = ["Origin", "Access-Control-Request-Headers", "Access-Control-Request-Method"]
    }
  }
  
  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  } 

  viewer_certificate {
    acm_certificate_arn = data.aws_acm_certificate.wildcard.arn
    ssl_support_method = "sni-only"
  }
  
  tags = {
    Name = "${var.SERVICE_PREFIX[terraform.workspace]}-mcf"
  }

  depends_on = [ aws_cloudfront_origin_access_control.s3 ]
}

resource "aws_s3_bucket_cors_configuration" "mb" {
  bucket = data.aws_s3_bucket.mb.id
  cors_rule {
    allowed_origins  = ["*"]
    allowed_methods  = ["GET", "PUT", "POST", "DELETE", "HEAD"]
    allowed_headers  = ["*"]
    expose_headers   = ["ETag"]
  }
}

resource "aws_s3_bucket_policy" "mcf_to_mb" {
  bucket = data.aws_s3_bucket.mb.id
  policy = data.aws_iam_policy_document.mcf_to_mb.json
}
