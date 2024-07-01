data "aws_route53_zone" "zone" {
  name         = var.domain_zone
  private_zone = false
}

resource "aws_route53_record" "route" {
  for_each = {
    for dvo in aws_acm_certificate.certificate.domain_validation_options : dvo.domain_name => {
      name   = dvo.resource_record_name
      record = dvo.resource_record_value
      type   = dvo.resource_record_type
    }
  }

  allow_overwrite = true
  name            = each.value.name
  records         = [each.value.record]
  ttl             = 60
  type            = each.value.type
  zone_id         = data.aws_route53_zone.zone.zone_id
}

resource "aws_route53_record" "cname" {
  zone_id = data.aws_route53_zone.zone.id
  name    = var.domain_name
  type    = "CNAME"
  ttl     = "5"
  records = [
    aws_api_gateway_domain_name.domain.regional_domain_name
  ]
}
