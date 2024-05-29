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

/**
 * NEW DNS Zone (all under record-locator.national.nhs.uk)
 */
resource "aws_route53_record" "NEW_ref_zone_delegation" {
  zone_id = aws_route53_zone.prod_zone.zone_id
  name    = "ref.record-locator.national.nhs.uk"
  records = [
    "ns-1654.awsdns-14.co.uk.",
    "ns-1328.awsdns-38.org.",
    "ns-47.awsdns-05.com.",
    "ns-834.awsdns-40.net."
  ]
  ttl  = 300
  type = "NS"
}

resource "aws_route53_record" "NEW_int_zone_delegation" {
  zone_id = aws_route53_zone.prod_zone.zone_id
  name    = "int.record-locator.national.nhs.uk"
  records = [
    "ns-1064.awsdns-05.org.",
    "ns-609.awsdns-12.net.",
    "ns-2014.awsdns-59.co.uk.",
    "ns-386.awsdns-48.com."
  ]
  ttl  = 300
  type = "NS"
}

resource "aws_route53_record" "NEW_dev_zone_delegation" {
  zone_id = aws_route53_zone.prod_zone.zone_id
  name    = "dev.record-locator.national.nhs.uk"
  records = [
    "ns-1331.awsdns-38.org.",
    "ns-160.awsdns-20.com.",
    "ns-1900.awsdns-45.co.uk.",
    "ns-962.awsdns-56.net."
  ]
  ttl  = 300
  type = "NS"
}

// TODO-NOW - Get these QA zone changes reflected in mgmt account (w/ Tom or Kate)
resource "aws_route53_zone" "qa_zone" {
  name = "qa.record-locator.national.nhs.uk"

  tags = {
    Environment = terraform.workspace
  }
}

resource "aws_route53_record" "qa_zone_delegation" {
  zone_id = aws_route53_zone.prod_zone.zone_id
  name    = "qa.record-locator.national.nhs.uk"
  records = [
    "ns-1821.awsdns-35.co.uk.",
    "ns-1449.awsdns-53.org.",
    "ns-933.awsdns-52.net.",
    "ns-500.awsdns-62.com."
  ]
  ttl  = 300
  type = "NS"
}
