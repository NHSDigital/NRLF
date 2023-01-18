data "aws_route53_zone" "zone" {
  name         = local.apis.zone
  private_zone = false
}

resource "aws_acm_certificate" "certificate" {
  domain_name = local.apis.domain
  subject_alternative_names = [
    local.apis.domain
  ]
  validation_method = "DNS"

  lifecycle {
    create_before_destroy = true
  }
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

resource "aws_acm_certificate_validation" "validation" {
  certificate_arn         = aws_acm_certificate.certificate.arn
  validation_record_fqdns = [for record in aws_route53_record.route : record.fqdn]
}

resource "aws_api_gateway_domain_name" "domain" {
  domain_name              = aws_acm_certificate.certificate.domain_name
  regional_certificate_arn = aws_acm_certificate.certificate.arn
  endpoint_configuration {
    types = ["REGIONAL"]
  }
  depends_on = [
    aws_acm_certificate_validation.validation
  ]
}

resource "aws_route53_record" "cname" {
  zone_id = data.aws_route53_zone.zone.id
  name    = local.apis.domain
  type    = "CNAME"
  ttl     = "5"
  records = [
    aws_api_gateway_domain_name.domain.regional_domain_name
  ]
}

output "zone" {
  value = local.apis.zone
}

output "domain" {
  value = local.apis.domain
}
