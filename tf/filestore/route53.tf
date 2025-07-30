resource "aws_route53_record" "api_a_record" {
  zone_id = data.aws_route53_zone.root.zone_id
  name    = var.API_FQDN[terraform.workspace]
  type    = "CNAME"
  ttl     = 86400
  
  records = [
    var.LOCAL_FQDN[terraform.workspace]
  ]
}

resource "aws_route53_record" "mcf_a_record" {
  zone_id = data.aws_route53_zone.root.zone_id
  name    = var.MEDIA_CDN_FQDN[terraform.workspace]
  type    = "A"
  
  alias {
    name                   = aws_cloudfront_distribution.mcf.domain_name
    zone_id                = aws_cloudfront_distribution.mcf.hosted_zone_id
    evaluate_target_health = false
  }
  
  depends_on = [ aws_cloudfront_distribution.mcf ]
}