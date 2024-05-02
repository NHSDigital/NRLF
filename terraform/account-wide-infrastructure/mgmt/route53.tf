resource "aws_route53_zone" "prod_zone" {
  name = "record-locator.national.nhs.uk"

  tags = {
    Environment = terraform.workspace
  }
}

resource "aws_route53_record" "prod_zone" {
  zone_id = aws_route53_zone.prod_zone.zone_id
  name    = "api.record-locator.national.nhs.uk"
  records = [
    "ns-1269.awsdns-30.org.",
    "ns-729.awsdns-27.net.",
    "ns-1680.awsdns-18.co.uk.",
    "ns-237.awsdns-29.com."
  ]
  ttl  = 300
  type = "NS"
}

resource "aws_route53_zone" "ref_zone" {
  name = "record-locator.ref.national.nhs.uk"

  tags = {
    Environment = terraform.workspace
  }
}

resource "aws_route53_record" "ref_zone" {
  zone_id = aws_route53_zone.ref_zone.zone_id
  name    = "api.record-locator.ref.national.nhs.uk"
  records = [
    "ns-1982.awsdns-55.co.uk.",
    "ns-1513.awsdns-61.org.",
    "ns-765.awsdns-31.net.",
    "ns-257.awsdns-32.com."
  ]
  ttl  = 300
  type = "NS"
}

resource "aws_route53_zone" "int_zone" {
  name = "record-locator.int.national.nhs.uk"

  tags = {
    Environment = terraform.workspace
  }
}

resource "aws_route53_record" "int_zone" {
  zone_id = aws_route53_zone.int_zone.zone_id
  name    = "api."
  records = [
    "ns-1877.awsdns-42.co.uk.",
    "ns-279.awsdns-34.com.",
    "ns-789.awsdns-34.net.",
    "ns-1362.awsdns-42.org."
  ]
  ttl  = 300
  type = "NS"
}

resource "aws_route53_zone" "qa_zone" {
  name = "record-locator.qa.national.nhs.uk"

  tags = {
    Environment = terraform.workspace
  }
}

resource "aws_route53_record" "qa_zone" {
  zone_id = aws_route53_zone.qa_zone.zone_id
  name    = "api.record-locator.qa.national.nhs.uk"
  records = [
    // TODO-NOW - Create the zone in test account and add NS here
  ]
  ttl  = 300
  type = "NS"
}

resource "aws_route53_zone" "dev_zone" {
  name = "record-locator.dev.national.nhs.uk"

  tags = {
    Environment = terraform.workspace
  }
}

resource "aws_route53_record" "dev_zone" {
  zone_id = aws_route53_zone.dev_zone.zone_id
  name    = "api.record-locator.dev.national.nhs.uk"
  records = [
    "ns-495.awsdns-61.com.",
    "ns-610.awsdns-12.net.",
    "ns-1934.awsdns-49.co.uk.",
    "ns-1382.awsdns-44.org."
  ]
  ttl  = 300
  type = "NS"
}
